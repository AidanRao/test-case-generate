from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ReportTemplateDefinition:
    template_id: str
    name: str
    filename: str
    profile_id: str


@dataclass(frozen=True)
class ResolvedReportTemplate:
    template_id: str
    name: str
    path: str
    profile_id: str


def _build_template_index(definitions):
    index = {definition.template_id: definition for definition in definitions}
    if len(index) != len(definitions):
        raise ValueError("Word 报告 template_id 不能重复")
    return index


_TEMPLATE_DEFINITIONS = (
    ReportTemplateDefinition(
        template_id="standard_test_case_word_report",
        name="标准测试用例文档",
        filename="test_case_report.docx",
        profile_id="standard",
    ),
)

_TEMPLATES_BY_ID = _build_template_index(_TEMPLATE_DEFINITIONS)


def _template_path(base_dir, definition):
    return os.path.join(base_dir, "template", definition.filename)


def resolve_template(base_dir, template_id):
    definition = _TEMPLATES_BY_ID.get(template_id)
    if definition is None:
        return None
    return ResolvedReportTemplate(
        template_id=definition.template_id,
        name=definition.name,
        path=_template_path(base_dir, definition),
        profile_id=definition.profile_id,
    )


def available_templates(base_dir):
    return tuple(
        {
            "template_id": definition.template_id,
            "name": definition.name,
        }
        for definition in _TEMPLATE_DEFINITIONS
        if os.path.isfile(_template_path(base_dir, definition))
    )


def registered_template_ids():
    return tuple(
        definition.template_id for definition in _TEMPLATE_DEFINITIONS
    )
