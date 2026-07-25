from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ReportTemplateDefinition:
    template_id: str
    name: str
    filename: str
    title_marker: str
    body_anchor_strategy: str


@dataclass(frozen=True)
class ReportTemplate:
    template_id: str
    name: str
    path: str
    title_marker: str
    body_anchor_strategy: str


_TEMPLATES = {
    "default": ReportTemplateDefinition(
        template_id="default",
        name="标准测试用例文档",
        filename="test_case_report.docx",
        title_marker="xx测试报告",
        body_anchor_strategy="last_body_paragraph",
    )
}


def _template_path(base_dir, definition):
    return os.path.join(base_dir, "template", definition.filename)


def resolve_template(base_dir, template_id):
    definition = _TEMPLATES.get(template_id)
    if definition is None:
        return None
    return ReportTemplate(
        template_id=definition.template_id,
        name=definition.name,
        path=_template_path(base_dir, definition),
        title_marker=definition.title_marker,
        body_anchor_strategy=definition.body_anchor_strategy,
    )


def available_templates(base_dir):
    return tuple(
        {
            "template_id": definition.template_id,
            "name": definition.name,
        }
        for definition in _TEMPLATES.values()
        if os.path.isfile(_template_path(base_dir, definition))
    )


def registered_template_ids():
    return tuple(_TEMPLATES)
