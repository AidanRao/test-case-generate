import os
import tempfile

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docxtpl import DocxTemplate


BODY_ANCHOR = "__TEST_CASE_REPORT_BODY__"
CHINESE_FONT = "宋体"
LATIN_FONT = "Times New Roman"
BODY_SIZE = 12
TABLE_WIDTHS = (720, 4140, 3450)


class ReportRenderError(RuntimeError):
    pass


def _set_font(element, size=BODY_SIZE, bold=None):
    element.font.name = LATIN_FONT
    element.font.size = Pt(size)
    if bold is not None:
        element.font.bold = bold
    r_pr = element._element.get_or_add_rPr()
    r_fonts = r_pr.get_or_add_rFonts()
    r_fonts.set(qn("w:ascii"), LATIN_FONT)
    r_fonts.set(qn("w:hAnsi"), LATIN_FONT)
    r_fonts.set(qn("w:cs"), LATIN_FONT)
    r_fonts.set(qn("w:eastAsia"), CHINESE_FONT)


def _set_run_font(run, size=BODY_SIZE, bold=None):
    run.font.name = LATIN_FONT
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.get_or_add_rFonts()
    r_fonts.set(qn("w:ascii"), LATIN_FONT)
    r_fonts.set(qn("w:hAnsi"), LATIN_FONT)
    r_fonts.set(qn("w:cs"), LATIN_FONT)
    r_fonts.set(qn("w:eastAsia"), CHINESE_FONT)


def _clear_paragraph(paragraph):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def _prepare_template(source_path, output_path, title_marker):
    document = Document(source_path)
    title_paragraph = next(
        (paragraph for paragraph in document.paragraphs if paragraph.text == title_marker),
        None,
    )
    if title_paragraph is None or not title_paragraph.runs:
        raise ReportRenderError("Word 模板缺少封面标题标记")
    title_paragraph.runs[0].text = "{{ project_title }}"

    if not document.paragraphs:
        raise ReportRenderError("Word 模板缺少正文锚点")
    body_anchor = document.paragraphs[-1]
    _clear_paragraph(body_anchor)
    body_anchor.add_run("{{ body_anchor }}")
    document.save(output_path)


def _get_or_create_style(
    document, name, size, bold, before, after, line_spacing=1.5
):
    try:
        style = document.styles[name]
    except KeyError:
        style = document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    _set_font(style, size=size, bold=bold)
    style.paragraph_format.space_before = Pt(before)
    style.paragraph_format.space_after = Pt(after)
    style.paragraph_format.line_spacing = line_spacing
    return style


def _configure_heading_style(style, size, before, after, outline_level):
    _set_font(style, size=size, bold=True)
    style.paragraph_format.space_before = Pt(before)
    style.paragraph_format.space_after = Pt(after)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.keep_with_next = True
    style.paragraph_format.keep_together = True

    paragraph_properties = style._element.get_or_add_pPr()
    outline = paragraph_properties.find(qn("w:outlineLvl"))
    if outline is None:
        outline = OxmlElement("w:outlineLvl")
        paragraph_properties.append(outline)
    outline.set(qn("w:val"), str(outline_level))


def _configure_styles(document):
    _get_or_create_style(document, "Report Body", BODY_SIZE, False, 0, 6)
    _get_or_create_style(
        document,
        "Report Metadata",
        BODY_SIZE,
        False,
        0,
        2,
        line_spacing=1.15,
    )
    _get_or_create_style(document, "Report Step Label", 12, True, 6, 4)
    _configure_heading_style(document.styles["Heading 1"], 16, 12, 8, 0)
    _configure_heading_style(document.styles["Heading 2"], 14, 10, 6, 1)
    _configure_heading_style(document.styles["Heading 3"], 12, 8, 4, 2)


def _add_text_paragraph(anchor, text, style, keep_with_next=False):
    paragraph = anchor.insert_paragraph_before(style=style)
    run = paragraph.add_run(str(text))
    _set_run_font(run, size=paragraph.style.font.size.pt if paragraph.style.font.size else BODY_SIZE)
    paragraph.paragraph_format.keep_with_next = keep_with_next
    return paragraph


def _add_metadata_paragraph(anchor, label, value):
    paragraph = anchor.insert_paragraph_before(style="Report Metadata")
    label_run = paragraph.add_run(f"{label}：")
    _set_run_font(label_run, bold=True)
    value_run = paragraph.add_run(str(value))
    _set_run_font(value_run)
    return paragraph


def _set_cell_margins(cell, top=120, start=120, bottom=120, end=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _set_cell_width(cell, width):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.first_child_found_in("w:tcW")
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width))
    tc_w.set(qn("w:type"), "dxa")


def _set_table_geometry(table):
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    tbl_w.set(qn("w:w"), str(sum(TABLE_WIDTHS)))
    tbl_w.set(qn("w:type"), "dxa")

    tbl_layout = tbl_pr.first_child_found_in("w:tblLayout")
    if tbl_layout is None:
        tbl_layout = OxmlElement("w:tblLayout")
        tbl_pr.append(tbl_layout)
    tbl_layout.set(qn("w:type"), "fixed")

    tbl_ind = tbl_pr.first_child_found_in("w:tblInd")
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "120")
    tbl_ind.set(qn("w:type"), "dxa")

    grid_columns = list(table._tbl.tblGrid)
    for grid_column, width in zip(grid_columns, TABLE_WIDTHS):
        grid_column.set(qn("w:w"), str(width))

    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "4")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), "A6A6A6")

    for row in table.rows:
        row_pr = row._tr.get_or_add_trPr()
        if row_pr.find(qn("w:cantSplit")) is None:
            row_pr.append(OxmlElement("w:cantSplit"))
        for cell, width in zip(row.cells, TABLE_WIDTHS):
            _set_cell_width(cell, width)
            _set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def _format_table_cell(cell, text, bold=False, centered=False, fill=None):
    paragraph = cell.paragraphs[0]
    _clear_paragraph(paragraph)
    paragraph.style = "Report Body"
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.25
    paragraph.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT
    )
    run = paragraph.add_run(str(text))
    _set_run_font(run, bold=bold)
    if fill:
        tc_pr = cell._tc.get_or_add_tcPr()
        shading = tc_pr.first_child_found_in("w:shd")
        if shading is None:
            shading = OxmlElement("w:shd")
            tc_pr.append(shading)
        shading.set(qn("w:fill"), fill)


def _add_steps_table(document, anchor, steps):
    table = document.add_table(rows=1 + len(steps), cols=3)
    headers = ("序号", "测试步骤", "预期结果")
    for index, header in enumerate(headers):
        _format_table_cell(
            table.rows[0].cells[index],
            header,
            bold=True,
            centered=True,
            fill="D9EAF7",
        )
    header_pr = table.rows[0]._tr.get_or_add_trPr()
    header_pr.append(OxmlElement("w:tblHeader"))

    for row_index, step in enumerate(steps, start=1):
        _format_table_cell(table.rows[row_index].cells[0], row_index, centered=True)
        _format_table_cell(table.rows[row_index].cells[1], step["step_desc"])
        _format_table_cell(table.rows[row_index].cells[2], step["expectation"])

    _set_table_geometry(table)
    anchor._p.addprevious(table._tbl)
    spacer = anchor.insert_paragraph_before(style="Report Body")
    spacer.paragraph_format.space_after = Pt(2)


def _populate_body(document, anchor, context):
    modules = context.get("modules") or []
    if not modules:
        _add_text_paragraph(anchor, "暂无需求", "Report Body")
        return

    for module in modules:
        _add_text_paragraph(
            anchor,
            f"模块：{module['name']}",
            "Heading 1",
            keep_with_next=True,
        )
        for requirement in module["requirements"]:
            _add_text_paragraph(
                anchor,
                f"需求：{requirement['title']}",
                "Heading 2",
                keep_with_next=True,
            )
            _add_metadata_paragraph(anchor, "需求编号", requirement["code"])
            _add_metadata_paragraph(anchor, "需求类型", requirement["type"])
            _add_metadata_paragraph(anchor, "需求内容", requirement["content"])

            if not requirement["testcases"]:
                _add_metadata_paragraph(anchor, "测试用例", "暂无")
                continue

            for case_index, testcase in enumerate(requirement["testcases"], start=1):
                _add_text_paragraph(
                    anchor,
                    f"{case_index}. {testcase['title']}",
                    "Heading 3",
                    keep_with_next=True,
                )
                _add_metadata_paragraph(anchor, "编号", testcase["code"])
                _add_metadata_paragraph(anchor, "类型", testcase["type"])
                _add_metadata_paragraph(anchor, "场景", testcase["scenario_type"])
                _add_metadata_paragraph(anchor, "优先级", testcase["priority"])
                _add_metadata_paragraph(anchor, "测试目标", testcase["test_target_desc"])
                _add_metadata_paragraph(anchor, "验证方法", testcase["verify_method"])
                if testcase["steps"]:
                    _add_text_paragraph(
                        anchor,
                        "测试步骤",
                        "Report Step Label",
                        keep_with_next=True,
                    )
                    _add_steps_table(document, anchor, testcase["steps"])
                else:
                    _add_metadata_paragraph(anchor, "测试步骤", "暂无")


def _enable_field_updates(document):
    settings = document.settings._element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")


class WordReportRenderer:
    def render(self, context, template, output_path):
        if not os.path.isfile(template.path):
            raise ReportRenderError("Word 模板不存在")
        with tempfile.TemporaryDirectory(prefix="test-report-render-") as temp_dir:
            prepared_path = os.path.join(temp_dir, "prepared.docx")
            rendered_path = os.path.join(temp_dir, "rendered.docx")
            _prepare_template(template.path, prepared_path, template.title_marker)

            doc_template = DocxTemplate(prepared_path)
            doc_template.render(
                {
                    "project_title": context["project"]["title"],
                    "body_anchor": BODY_ANCHOR,
                },
                autoescape=True,
            )
            doc_template.save(rendered_path)

            document = Document(rendered_path)
            _configure_styles(document)
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

            title_text = f"{context['project']['title']}测试报告"
            title = next(
                (
                    paragraph
                    for paragraph in document.paragraphs
                    if paragraph.text == title_text
                ),
                None,
            )
            if title is not None:
                for run in title.runs:
                    _set_run_font(run, size=24, bold=True)

            _populate_body(document, anchor, context)
            anchor._element.getparent().remove(anchor._element)
            _enable_field_updates(document)
            document.core_properties.title = title_text
            document.save(output_path)
