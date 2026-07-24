from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ReportTemplate:
    template_id: str
    path: str
    title_marker: str
    body_anchor_strategy: str


_TEMPLATES = {
    "default": {
        "filename": "test_case_report.docx",
        "title_marker": "xx测试报告",
        "body_anchor_strategy": "last_body_paragraph",
    }
}


def resolve_template(base_dir, template_id):
    definition = _TEMPLATES.get(template_id)
    if definition is None:
        return None
    return ReportTemplate(
        template_id=template_id,
        path=os.path.join(base_dir, "template", definition["filename"]),
        title_marker=definition["title_marker"],
        body_anchor_strategy=definition["body_anchor_strategy"],
    )


def registered_template_ids():
    return tuple(_TEMPLATES)

