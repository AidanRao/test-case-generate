from dataclasses import dataclass
from typing import Callable

from app.reports.document import (
    CellMargins,
    HeadingStyle,
    WordReportTheme,
)
from app.reports.sections import (
    DocumentOverviewSection,
    ReportSection,
    RequirementDetailsSection,
    RequirementOverviewSection,
)


class ReportProfileConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class WordReportProfile:
    profile_id: str
    document_title_factory: Callable[[dict], str]
    section_factories: tuple[Callable[[], ReportSection], ...]
    theme: WordReportTheme

    def document_title(self, context):
        return self.document_title_factory(context)

    def create_sections(self):
        return tuple(factory() for factory in self.section_factories)


STANDARD_WORD_REPORT_THEME = WordReportTheme(
    chinese_font="宋体",
    latin_font="Times New Roman",
    body_size=12,
    body_space_before=0,
    body_space_after=6,
    body_line_spacing=1.5,
    metadata_size=12,
    metadata_space_before=0,
    metadata_space_after=2,
    metadata_line_spacing=1.15,
    step_label_size=12,
    step_label_space_before=6,
    step_label_space_after=4,
    step_label_line_spacing=1.5,
    table_font_size=10.5,
    table_indent=120,
    table_border_color="A6A6A6",
    table_header_fill="D9EAF7",
    table_cell_margins=CellMargins(
        top=120,
        start=120,
        bottom=120,
        end=120,
    ),
    heading_styles=(
        HeadingStyle(
            size=16,
            space_before=12,
            space_after=8,
            outline_level=0,
        ),
        HeadingStyle(
            size=14,
            space_before=10,
            space_after=6,
            outline_level=1,
        ),
        HeadingStyle(
            size=12,
            space_before=8,
            space_after=4,
            outline_level=2,
        ),
        HeadingStyle(
            size=12,
            space_before=6,
            space_after=4,
            outline_level=3,
        ),
    ),
)


def _standard_document_title(context):
    return f"{context['project']['title']}测试用例文档"


_REPORT_PROFILES = {
    "standard": WordReportProfile(
        profile_id="standard",
        document_title_factory=_standard_document_title,
        section_factories=(
            DocumentOverviewSection,
            RequirementOverviewSection,
            RequirementDetailsSection,
        ),
        theme=STANDARD_WORD_REPORT_THEME,
    ),
}


def resolve_report_profile(profile_id):
    try:
        return _REPORT_PROFILES[profile_id]
    except KeyError as exc:
        raise ReportProfileConfigurationError(
            f"未注册的 Word 报告 profile: {profile_id}"
        ) from exc
