import os
import tempfile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docxtpl import DocxTemplate

from app.reports.document import WordDocumentComposer, set_run_font
from app.reports.sections import (
    DocumentOverviewSection,
    RequirementDetailsSection,
    RequirementOverviewSection,
)


BODY_ANCHOR = "__TEST_CASE_REPORT_BODY__"


class ReportRenderError(RuntimeError):
    pass


def _clear_paragraph(paragraph):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def _prepare_template(source_path, output_path, title_marker):
    document = Document(source_path)
    title_paragraph = next(
        (
            paragraph
            for paragraph in document.paragraphs
            if paragraph.text == title_marker
        ),
        None,
    )
    if title_paragraph is None or not title_paragraph.runs:
        raise ReportRenderError("Word 模板缺少封面标题标记")
    _clear_paragraph(title_paragraph)
    title_paragraph.add_run("{{ document_title }}")

    if not document.paragraphs:
        raise ReportRenderError("Word 模板缺少正文锚点")
    body_anchor = document.paragraphs[-1]
    _clear_paragraph(body_anchor)
    body_anchor.add_run("{{ body_anchor }}")
    document.save(output_path)


def _enable_field_updates(document):
    settings = document.settings._element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")


class WordReportRenderer:
    def __init__(self, sections=None):
        self._sections = tuple(
            sections
            if sections is not None
            else (
                DocumentOverviewSection(),
                RequirementOverviewSection(),
                RequirementDetailsSection(),
            )
        )

    def render(self, context, template, output_path):
        if not os.path.isfile(template.path):
            raise ReportRenderError("Word 模板不存在")

        with tempfile.TemporaryDirectory(
            prefix="test-report-render-"
        ) as temp_dir:
            rendered_path = self._render_shell(context, template, temp_dir)
            document = Document(rendered_path)
            anchor = self._find_anchor(document)
            composer = WordDocumentComposer(document, anchor)

            document_title = context["metadata"]["document_name"]
            self._format_cover_title(document, document_title)
            for section in self._sections:
                section.render(composer, context)

            anchor._element.getparent().remove(anchor._element)
            _enable_field_updates(document)
            document.core_properties.title = document_title
            document.save(output_path)

    @staticmethod
    def _render_shell(context, template, temp_dir):
        prepared_path = os.path.join(temp_dir, "prepared.docx")
        rendered_path = os.path.join(temp_dir, "rendered.docx")
        _prepare_template(
            template.path,
            prepared_path,
            template.title_marker,
        )

        doc_template = DocxTemplate(prepared_path)
        doc_template.render(
            {
                "document_title": context["metadata"]["document_name"],
                "body_anchor": BODY_ANCHOR,
            },
            autoescape=True,
        )
        doc_template.save(rendered_path)
        return rendered_path

    @staticmethod
    def _find_anchor(document):
        anchor = next(
            (
                paragraph
                for paragraph in document.paragraphs
                if paragraph.text == BODY_ANCHOR
            ),
            None,
        )
        if anchor is None:
            raise ReportRenderError("Word 模板正文锚点渲染失败")
        return anchor

    @staticmethod
    def _format_cover_title(document, document_title):
        title = next(
            (
                paragraph
                for paragraph in document.paragraphs
                if paragraph.text == document_title
            ),
            None,
        )
        if title is None:
            return
        for run in title.runs:
            set_run_font(run, size=24, bold=True)
