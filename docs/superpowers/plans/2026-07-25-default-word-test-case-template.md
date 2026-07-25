# Default Word Test Case Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the backend `default` Word export with a three-chapter test case document containing document metadata, grouped statistics, coverage analysis, and module/requirement/test-case details.

**Architecture:** A `ReportContextBuilder` normalizes source records and computes all report statistics independently of Word. A reusable `WordDocumentComposer` owns `python-docx` formatting and table mechanics, while three `ReportSection` implementations own chapter content; `WordReportRenderer` only prepares the shell template and orchestrates the sections.

**Tech Stack:** Python 3.11, Flask 3.1.2, python-docx 1.2.0, docxtpl 0.20.2, unittest, conda environment `test-case-generate`.

## Global Constraints

- Backend only; do not modify frontend files or frontend request behavior.
- `template_id=default` must directly render the new document structure.
- The document has exactly three top-level chapters: `一、文档概述`, `二、需求与用例概述`, and `三、需求与测试用例明细`.
- Requirement coverage is `已覆盖` when at least one test case is linked and `未覆盖` otherwise; do not emit `部分覆盖`.
- Requirement statistics are grouped by module, and the module cell is vertically merged for adjacent requirements in the same module.
- The document version is `V1.0`; the compilation date is the export date in `YYYY-MM-DD` format.
- Preserve the template cover, sections, headers, footers, and page number field.
- Preserve user-owned unrelated changes, including the untracked `readme.md`.

---

## File Structure

- Modify `backend/app/reports/context_builder.py`: replace the function-oriented builder with a testable `ReportContextBuilder` that normalizes records and calculates summaries.
- Create `backend/app/reports/document.py`: encapsulate Word styles, headings, paragraphs, generic tables, step tables, geometry, and vertical cell merging.
- Create `backend/app/reports/sections.py`: define the report-section interface and the three concrete chapter renderers.
- Modify `backend/app/reports/renderer.py`: retain template preparation and final document handling, and delegate body generation to section objects.
- Modify `backend/app/routes/testcases.py`: instantiate `ReportContextBuilder` rather than calling the removed function.
- Replace `backend/template/test_case_report.docx`: copy the approved `test_case_report-v2.docx` shell over the tracked default template path so the registry and API contract remain stable.
- Create `backend/tests/test_report_context.py`: unit-test normalized context and summary calculations without Word.
- Create `backend/tests/test_word_sections.py`: render the real section objects into an in-memory document and test chapter tables, heading hierarchy, and vertical merge behavior.
- Modify `backend/tests/test_word_report_export.py`: update the API-level expectations for the new default document and preserve template/layout/error regressions.

---

### Task 1: Build the Report Context and Statistics

**Files:**

- Create: `backend/tests/test_report_context.py`
- Modify: `backend/app/reports/context_builder.py`

**Interfaces:**

- Produces: `ReportContextBuilder(today_provider: Callable[[], date] | None = None)`
- Produces: `ReportContextBuilder.build(source: dict) -> dict`
- The returned dictionary has `metadata`, `project`, `modules`, and `summary` keys.
- `summary` contains `requirement_groups`, `case_type_stats`, `priority_stats`, and `coverage`.
- Later tasks consume only this public context shape and do not perform business aggregation themselves.

- [ ] **Step 1: Write a failing context test for metadata, module grouping, statistics, and coverage**

Create `backend/tests/test_report_context.py` with a literal fixture. The production change caught by this test is returning raw records without the required normalized metadata and calculated summaries.

```python
from datetime import date
import unittest

from app.reports.context_builder import ReportContextBuilder


SOURCE = {
    "project": {"id": "p-1", "code": "PRJ-01", "title": "示例系统"},
    "requirements": [
        {
            "id": "r-1",
            "code": "REQ-001",
            "title": "用户登录",
            "type": "功能需求",
            "content": "账号密码登录",
            "module": "认证",
        },
        {
            "id": "r-2",
            "code": "REQ-002",
            "title": "用户注册",
            "type": "功能需求",
            "content": "注册新账号",
            "module": "认证",
        },
        {
            "id": "r-3",
            "code": "REQ-003",
            "title": "审计记录",
            "type": "",
            "content": "",
            "module": "审计",
        },
    ],
    "testcases": [
        {
            "id": "tc-1",
            "requirement_id": "r-1",
            "code": "TC-LOGIN-001",
            "title": "登录成功",
            "type": "功能测试",
            "scenario_type": "正常流程用例",
            "priority": "P0",
            "test_steps": [],
        },
        {
            "id": "tc-2",
            "requirement_id": "r-1",
            "code": "TC-LOGIN-002",
            "title": "密码错误",
            "type": "安全性测试",
            "scenario_type": "异常场景用例",
            "priority": "",
            "test_steps": [],
        },
        {
            "id": "tc-3",
            "requirement_id": "r-2",
            "code": "TC-REGISTER-001",
            "title": "注册成功",
            "type": "功能测试",
            "scenario_type": "正常流程用例",
            "priority": "P1",
            "test_steps": [],
        },
    ],
}


class ReportContextBuilderTest(unittest.TestCase):
    def setUp(self):
        self.context = ReportContextBuilder(
            today_provider=lambda: date(2026, 7, 25)
        ).build(SOURCE)

    def test_builds_document_metadata_and_grouped_requirement_summary(self):
        self.assertEqual(
            self.context["metadata"],
            {
                "document_name": "示例系统测试用例文档",
                "project_name": "示例系统",
                "version": "V1.0",
                "compiled_date": "2026-07-25",
            },
        )
        self.assertEqual(
            self.context["summary"]["requirement_groups"],
            [
                {
                    "module": "认证",
                    "requirements": [
                        {
                            "code": "REQ-001",
                            "title": "用户登录",
                            "type": "功能需求",
                            "testcase_count": 2,
                        },
                        {
                            "code": "REQ-002",
                            "title": "用户注册",
                            "type": "功能需求",
                            "testcase_count": 1,
                        },
                    ],
                },
                {
                    "module": "审计",
                    "requirements": [
                        {
                            "code": "REQ-003",
                            "title": "审计记录",
                            "type": "未知类型",
                            "testcase_count": 0,
                        }
                    ],
                },
            ],
        )

    def test_calculates_case_type_priority_and_coverage_summaries(self):
        self.assertEqual(
            self.context["summary"]["case_type_stats"],
            [
                {"name": "功能测试", "count": 2, "percentage": "66.67%"},
                {"name": "安全性测试", "count": 1, "percentage": "33.33%"},
            ],
        )
        self.assertEqual(
            self.context["summary"]["priority_stats"],
            [{"name": "P0", "count": 1, "percentage": "33.33%"},
             {"name": "P1", "count": 2, "percentage": "66.67%"}],
        )
        self.assertEqual(
            self.context["summary"]["coverage"],
            [
                {
                    "code": "REQ-001",
                    "title": "用户登录",
                    "testcase_codes": "TC-LOGIN-001、TC-LOGIN-002",
                    "testcase_count": 2,
                    "status": "已覆盖",
                },
                {
                    "code": "REQ-002",
                    "title": "用户注册",
                    "testcase_codes": "TC-REGISTER-001",
                    "testcase_count": 1,
                    "status": "已覆盖",
                },
                {
                    "code": "REQ-003",
                    "title": "审计记录",
                    "testcase_codes": "暂无",
                    "testcase_count": 0,
                    "status": "未覆盖",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the context test and verify the expected failure**

Run:

```bash
cd backend
conda run -n test-case-generate python tests/test_report_context.py
```

Expected: FAIL because `ReportContextBuilder` does not exist.

- [ ] **Step 3: Implement the minimal object-oriented context builder**

Replace the public function in `backend/app/reports/context_builder.py` with the class below, retaining the existing display normalization and orphan-case behavior in private helpers:

```python
from collections import Counter
from datetime import date

from app.models.testcase import DEFAULT_PRIORITY


class ReportContextBuilder:
    def __init__(self, today_provider=None):
        self._today_provider = today_provider or date.today

    def build(self, source):
        project = source["project"]
        modules = self._build_modules(
            source.get("requirements") or [],
            source.get("testcases") or [],
        )
        project_name = self._project_name(project)
        return {
            "metadata": {
                "document_name": f"{project_name}测试用例文档",
                "project_name": project_name,
                "version": "V1.0",
                "compiled_date": self._today_provider().isoformat(),
            },
            "project": {
                "id": str(project.get("id") or ""),
                "code": _display(
                    project.get("code"),
                    str(project.get("id") or "project"),
                ),
                "title": project_name,
            },
            "modules": modules,
            "summary": self._build_summary(modules),
        }

    def _build_summary(self, modules):
        requirements = [
            requirement
            for module in modules
            for requirement in module["requirements"]
        ]
        testcases = [
            testcase
            for requirement in requirements
            for testcase in requirement["testcases"]
        ]
        return {
            "requirement_groups": [
                {
                    "module": module["name"],
                    "requirements": [
                        {
                            "code": requirement["code"],
                            "title": requirement["title"],
                            "type": requirement["type"],
                            "testcase_count": len(requirement["testcases"]),
                        }
                        for requirement in module["requirements"]
                    ],
                }
                for module in modules
            ],
            "case_type_stats": self._statistics(
                testcase["type"] for testcase in testcases
            ),
            "priority_stats": self._statistics(
                testcase["priority"] for testcase in testcases
            ),
            "coverage": [
                {
                    "code": requirement["code"],
                    "title": requirement["title"],
                    "testcase_codes": "、".join(
                        testcase["code"]
                        for testcase in requirement["testcases"]
                    ) or EMPTY_VALUE,
                    "testcase_count": len(requirement["testcases"]),
                    "status": (
                        "已覆盖" if requirement["testcases"] else "未覆盖"
                    ),
                }
                for requirement in requirements
            ],
        }

    @staticmethod
    def _statistics(values):
        counts = Counter(values)
        total = sum(counts.values())
        return [
            {
                "name": name,
                "count": count,
                "percentage": f"{count / total:.2%}",
            }
            for name, count in counts.items()
        ]
```

Implement `_project_name()` and `_build_modules()` by moving the existing title fallback and module/case association logic into methods. `_build_case()` must continue to normalize an empty priority to `DEFAULT_PRIORITY`, so the literal priority test above passes.

- [ ] **Step 4: Run the context tests and verify they pass**

Run:

```bash
cd backend
conda run -n test-case-generate python tests/test_report_context.py
```

Expected: 2 tests, OK.

- [ ] **Step 5: Add and pass a zero-data edge-case test**

Add a test whose production break is division by zero or omission of required empty summaries:

```python
def test_empty_project_has_empty_statistics_without_division_by_zero(self):
    context = ReportContextBuilder(
        today_provider=lambda: date(2026, 7, 25)
    ).build(
        {
            "project": {"id": "p-empty", "code": "EMPTY", "title": ""},
            "requirements": [],
            "testcases": [],
        }
    )

    self.assertEqual(context["metadata"]["document_name"], "EMPTY测试用例文档")
    self.assertEqual(context["modules"], [])
    self.assertEqual(
        context["summary"],
        {
            "requirement_groups": [],
            "case_type_stats": [],
            "priority_stats": [],
            "coverage": [],
        },
    )
```

Run the test before any corrective code. If it fails for the expected zero-data reason, make only the minimal builder correction, then rerun:

```bash
cd backend
conda run -n test-case-generate python tests/test_report_context.py
```

Expected: 3 tests, OK.

- [ ] **Step 6: Commit the context builder**

```bash
git add backend/app/reports/context_builder.py backend/tests/test_report_context.py
git commit -m "feat: 构建 Word 报告统计上下文"
```

---

### Task 2: Create Reusable Word Components and Chapter Renderers

**Files:**

- Create: `backend/app/reports/document.py`
- Create: `backend/app/reports/sections.py`
- Create: `backend/tests/test_word_sections.py`

**Interfaces:**

- Consumes: the Task 1 context dictionary.
- Produces: `WordDocumentComposer(document: Document, anchor: Paragraph)`.
- Produces: `WordDocumentComposer.add_heading(text: str, level: int)`.
- Produces: `WordDocumentComposer.add_metadata(label: str, value: str)`.
- Produces: `WordDocumentComposer.add_table(headers, rows, widths, centered_columns=(), merge_ranges=()) -> Table`.
- Produces: `WordDocumentComposer.add_steps_table(steps) -> Table`.
- Produces: abstract `ReportSection.render(composer, context) -> None`.
- Produces: `DocumentOverviewSection`, `RequirementOverviewSection`, and `RequirementDetailsSection`.

- [ ] **Step 1: Write a failing real-document test for all chapter content and heading levels**

Create `backend/tests/test_word_sections.py`. Use a real in-memory `Document`; do not mock `python-docx`. The production breaks caught are missing chapters, incorrect heading levels, missing summary tables, and flattened detail hierarchy.

```python
import unittest

from docx import Document

from app.reports.document import WordDocumentComposer
from app.reports.sections import (
    DocumentOverviewSection,
    RequirementDetailsSection,
    RequirementOverviewSection,
)


CONTEXT = {
    "metadata": {
        "document_name": "示例系统测试用例文档",
        "project_name": "示例系统",
        "version": "V1.0",
        "compiled_date": "2026-07-25",
    },
    "project": {"id": "p-1", "code": "PRJ-01", "title": "示例系统"},
    "modules": [
        {
            "name": "认证",
            "requirements": [
                {
                    "id": "r-1",
                    "code": "REQ-001",
                    "title": "用户登录",
                    "type": "功能需求",
                    "content": "账号密码登录",
                    "testcases": [
                        {
                            "id": "tc-1",
                            "code": "TC-LOGIN-001",
                            "title": "登录成功",
                            "type": "功能测试",
                            "scenario_type": "正常流程用例",
                            "priority": "P0",
                            "test_target_desc": "验证登录",
                            "verify_method": "TESTING",
                            "steps": [
                                {
                                    "step_desc": "输入账号密码",
                                    "expectation": "登录成功",
                                }
                            ],
                        }
                    ],
                },
                {
                    "id": "r-2",
                    "code": "REQ-002",
                    "title": "用户注册",
                    "type": "功能需求",
                    "content": "注册账号",
                    "testcases": [],
                },
            ],
        }
    ],
    "summary": {
        "requirement_groups": [
            {
                "module": "认证",
                "requirements": [
                    {
                        "code": "REQ-001",
                        "title": "用户登录",
                        "type": "功能需求",
                        "testcase_count": 1,
                    },
                    {
                        "code": "REQ-002",
                        "title": "用户注册",
                        "type": "功能需求",
                        "testcase_count": 0,
                    },
                ],
            }
        ],
        "case_type_stats": [
            {"name": "功能测试", "count": 1, "percentage": "100.00%"}
        ],
        "priority_stats": [
            {"name": "P0", "count": 1, "percentage": "100.00%"}
        ],
        "coverage": [
            {
                "code": "REQ-001",
                "title": "用户登录",
                "testcase_codes": "TC-LOGIN-001",
                "testcase_count": 1,
                "status": "已覆盖",
            },
            {
                "code": "REQ-002",
                "title": "用户注册",
                "testcase_codes": "暂无",
                "testcase_count": 0,
                "status": "未覆盖",
            },
        ],
    },
}


class WordSectionTest(unittest.TestCase):
    def setUp(self):
        self.document = Document()
        self.anchor = self.document.add_paragraph("__ANCHOR__")
        self.composer = WordDocumentComposer(self.document, self.anchor)
        for section in (
            DocumentOverviewSection(),
            RequirementOverviewSection(),
            RequirementDetailsSection(),
        ):
            section.render(self.composer, CONTEXT)

    def test_renders_three_chapters_and_four_level_detail_hierarchy(self):
        paragraphs = {
            paragraph.text: paragraph.style.name
            for paragraph in self.document.paragraphs
        }
        self.assertEqual(paragraphs["一、文档概述"], "Heading 1")
        self.assertEqual(paragraphs["二、需求与用例概述"], "Heading 1")
        self.assertEqual(paragraphs["三、需求与测试用例明细"], "Heading 1")
        self.assertEqual(paragraphs["需求统计"], "Heading 2")
        self.assertEqual(paragraphs["用例统计"], "Heading 2")
        self.assertEqual(paragraphs["按用例类型统计"], "Heading 3")
        self.assertEqual(paragraphs["按优先级统计"], "Heading 3")
        self.assertEqual(paragraphs["需求覆盖分析"], "Heading 2")
        self.assertEqual(paragraphs["模块：认证"], "Heading 2")
        self.assertEqual(paragraphs["需求：用户登录"], "Heading 3")
        self.assertEqual(paragraphs["1. 登录成功"], "Heading 4")

    def test_renders_metadata_statistics_coverage_and_steps(self):
        tables = {
            tuple(cell.text for cell in table.rows[0].cells): table
            for table in self.document.tables
        }
        metadata = tables[("字段", "内容")]
        self.assertEqual(
            [[cell.text for cell in row.cells] for row in metadata.rows[1:]],
            [
                ["文档名称", "示例系统测试用例文档"],
                ["项目名称", "示例系统"],
                ["文档版本", "V1.0"],
                ["编制日期", "2026-07-25"],
            ],
        )
        requirement_stats = tables[
            ("模块", "需求编号", "需求名称", "需求类型", "用例数量")
        ]
        self.assertEqual(requirement_stats.rows[1].cells[0].text, "认证")
        self.assertIs(
            requirement_stats.rows[1].cells[0]._tc,
            requirement_stats.rows[2].cells[0]._tc,
        )
        coverage = tables[
            ("需求编号", "需求名称", "关联用例", "用例数量", "覆盖状态")
        ]
        self.assertEqual(
            [cell.text for cell in coverage.rows[2].cells],
            ["REQ-002", "用户注册", "暂无", "0", "未覆盖"],
        )
        steps = tables[("序号", "测试步骤", "预期结果")]
        self.assertEqual(
            [cell.text for cell in steps.rows[1].cells],
            ["1", "输入账号密码", "登录成功"],
        )
```

- [ ] **Step 2: Run the section test and verify the expected import failure**

Run:

```bash
cd backend
conda run -n test-case-generate python tests/test_word_sections.py
```

Expected: FAIL because `app.reports.document` and `app.reports.sections` do not exist.

- [ ] **Step 3: Implement the reusable Word composer**

Move the low-level style/font/XML functions out of `renderer.py` into `document.py`, then expose them through this public class:

```python
class WordDocumentComposer:
    def __init__(self, document, anchor):
        self.document = document
        self.anchor = anchor
        configure_styles(document)

    def add_heading(self, text, level):
        return self._add_paragraph(
            text,
            f"Heading {level}",
            keep_with_next=True,
        )

    def add_metadata(self, label, value):
        paragraph = self.anchor.insert_paragraph_before(
            style="Report Metadata"
        )
        label_run = paragraph.add_run(f"{label}：")
        set_run_font(label_run, bold=True)
        value_run = paragraph.add_run(str(value))
        set_run_font(value_run)
        return paragraph

    def add_table(
        self,
        headers,
        rows,
        widths,
        centered_columns=(),
        merge_ranges=(),
    ):
        table = self.document.add_table(rows=1 + len(rows), cols=len(headers))
        self._populate_header(table, headers)
        for row_index, values in enumerate(rows, start=1):
            for column_index, value in enumerate(values):
                self._format_cell(
                    table.rows[row_index].cells[column_index],
                    value,
                    centered=column_index in centered_columns,
                )
        self._set_table_geometry(table, widths)
        for column, first_body_row, last_body_row in merge_ranges:
            table.cell(first_body_row + 1, column).merge(
                table.cell(last_body_row + 1, column)
            )
        self.anchor._p.addprevious(table._tbl)
        self._add_table_spacer()
        return table

    def add_steps_table(self, steps):
        rows = [
            (index, step["step_desc"], step["expectation"])
            for index, step in enumerate(steps, start=1)
        ]
        return self.add_table(
            ("序号", "测试步骤", "预期结果"),
            rows,
            (720, 4140, 3450),
            centered_columns=(0,),
        )
```

Generalize table geometry so it validates `len(widths) == len(headers)`, writes one grid width per column, repeats the first row with `w:tblHeader`, applies `w:cantSplit` to every row, and applies the existing fonts, margins, border, fill, and vertical alignment. Configure `Heading 4` with outline level `3`.

- [ ] **Step 4: Implement the report-section strategy objects**

Create `sections.py` with a small interface and three concrete renderers:

```python
from abc import ABC, abstractmethod


class ReportSection(ABC):
    @abstractmethod
    def render(self, composer, context):
        raise NotImplementedError


class DocumentOverviewSection(ReportSection):
    def render(self, composer, context):
        metadata = context["metadata"]
        composer.add_heading("一、文档概述", 1)
        composer.add_table(
            ("字段", "内容"),
            (
                ("文档名称", metadata["document_name"]),
                ("项目名称", metadata["project_name"]),
                ("文档版本", metadata["version"]),
                ("编制日期", metadata["compiled_date"]),
            ),
            (1800, 6510),
        )


class RequirementOverviewSection(ReportSection):
    def render(self, composer, context):
        composer.add_heading("二、需求与用例概述", 1)
        self._render_requirement_stats(composer, context["summary"])
        self._render_case_stats(composer, context["summary"])
        self._render_coverage(composer, context["summary"])


class RequirementDetailsSection(ReportSection):
    def render(self, composer, context):
        composer.add_heading("三、需求与测试用例明细", 1)
        if not context["modules"]:
            composer.add_body("暂无需求")
            return
        for module in context["modules"]:
            composer.add_heading(f"模块：{module['name']}", 2)
            for requirement in module["requirements"]:
                composer.add_heading(f"需求：{requirement['title']}", 3)
                composer.add_metadata("需求编号", requirement["code"])
                composer.add_metadata("需求类型", requirement["type"])
                composer.add_metadata("需求内容", requirement["content"])
                self._render_testcases(composer, requirement["testcases"])
```

In `_render_requirement_stats`, flatten each module group into table rows, put the module name only in the first row of each group, and record `(0, first_row, last_row)` only for groups with two or more requirements. Render the two case-stat tables with literal headers `("用例类型", "用例数量", "占比")` and `("优先级", "用例数量", "占比")`. Render an empty summary table with one body row `("暂无数据", "", "")`. Use the widths defined in the design:

```python
REQUIREMENT_WIDTHS = (1500, 1300, 2300, 1600, 1610)
STATISTIC_WIDTHS = (3500, 1800, 3010)
COVERAGE_WIDTHS = (1300, 1800, 3000, 1000, 1210)
```

In `_render_testcases`, use `Heading 4`, retain the existing metadata labels, render the real step table, and emit `测试用例：暂无` or `测试步骤：暂无` for valid empty states.

- [ ] **Step 5: Run the section test and make it pass**

Run:

```bash
cd backend
conda run -n test-case-generate python tests/test_word_sections.py
```

Expected: 2 tests, OK.

- [ ] **Step 6: Add and pass an empty-summary rendering test**

Add this behavior test:

```python
def test_empty_summaries_keep_table_headers_and_show_no_data(self):
    document = Document()
    anchor = document.add_paragraph("__ANCHOR__")
    composer = WordDocumentComposer(document, anchor)
    context = {
        "summary": {
            "requirement_groups": [],
            "case_type_stats": [],
            "priority_stats": [],
            "coverage": [],
        }
    }

    RequirementOverviewSection().render(composer, context)

    type_table = next(
        table
        for table in document.tables
        if [cell.text for cell in table.rows[0].cells]
        == ["用例类型", "用例数量", "占比"]
    )
    self.assertEqual(
        [cell.text for cell in type_table.rows[1].cells],
        ["暂无数据", "", ""],
    )
```

Run it first and observe a failure if empty data is not yet handled. Make the minimal section correction, then rerun:

```bash
cd backend
conda run -n test-case-generate python tests/test_word_sections.py
```

Expected: 3 tests, OK.

- [ ] **Step 7: Commit the Word components and sections**

```bash
git add backend/app/reports/document.py backend/app/reports/sections.py backend/tests/test_word_sections.py
git commit -m "feat: 渲染 Word 测试用例文档章节"
```

---

### Task 3: Wire the New Default Template Through the Export API

**Files:**

- Modify: `backend/app/reports/renderer.py`
- Modify: `backend/app/routes/testcases.py`
- Replace: `backend/template/test_case_report.docx` using `backend/template/test_case_report-v2.docx`
- Modify: `backend/tests/test_word_report_export.py`

**Interfaces:**

- Consumes: `ReportContextBuilder.build(source)` from Task 1.
- Consumes: `WordDocumentComposer` and the three section classes from Task 2.
- Produces: `WordReportRenderer(sections=None)`.
- Preserves: `WordReportRenderer.render(context, template, output_path)`.
- Preserves: `GET /v1/projects/{project_id}/testcases/export?format=docx&template_id=default`.

- [ ] **Step 1: Rewrite the API-level test expectations before production changes**

In `backend/tests/test_word_report_export.py`, change the hierarchy expectation to the three chapters and four heading levels:

```python
from datetime import date

expected_order = [
    "Flight 2026飞控项目测试用例文档",
    "一、文档概述",
    "二、需求与用例概述",
    "三、需求与测试用例明细",
    "模块：登录 Module 1",
    "需求：用户 Login 2026",
    "1. 正常 Login 01",
    "需求：无用例需求",
    "模块：审计",
    "需求：审计日志",
]
positions = [texts.index(value) for value in expected_order]
self.assertEqual(positions, sorted(positions))
self.assertEqual(
    paragraphs_by_text["模块：登录 Module 1"].style.name,
    "Heading 2",
)
self.assertEqual(
    paragraphs_by_text["需求：用户 Login 2026"].style.name,
    "Heading 3",
)
self.assertEqual(
    paragraphs_by_text["1. 正常 Login 01"].style.name,
    "Heading 4",
)
```

Add API-level assertions that identify tables by literal headers and verify:

```python
self.assertEqual(
    table_rows(metadata_table),
    [
        ["字段", "内容"],
        ["文档名称", "Flight 2026飞控项目测试用例文档"],
        ["项目名称", "Flight 2026飞控项目"],
        ["文档版本", "V1.0"],
        ["编制日期", "2026-07-25"],
    ],
)
self.assertEqual(
    [cell.text for cell in requirement_table.rows[1].cells],
    ["登录 Module 1", "REQ-LOGIN-01", "用户 Login 2026", "功能需求", "1"],
)
self.assertIs(
    requirement_table.rows[1].cells[0]._tc,
    requirement_table.rows[2].cells[0]._tc,
)
self.assertEqual(
    [cell.text for cell in coverage_table.rows[2].cells],
    ["REQ-EMPTY", "无用例需求", "暂无", "0", "未覆盖"],
)
self.assertEqual(
    table_rows(case_type_table),
    [
        ["用例类型", "用例数量", "占比"],
        ["功能测试", "2", "100.00%"],
    ],
)
self.assertEqual(
    table_rows(priority_table),
    [
        ["优先级", "用例数量", "占比"],
        ["P0", "1", "50.00%"],
        ["P1", "1", "50.00%"],
    ],
)
```

Patch the builder date at the source boundary so the export date assertion is deterministic:

```python
with patch(
    "app.reports.context_builder.date"
) as mocked_date:
    mocked_date.today.return_value = date(2026, 7, 25)
    response = self.client.get(...)
```

Prefer injecting a builder into the route if patching `date.today` proves brittle; assert only on the generated document, not on mock calls.

In `test_word_structure_preserves_fonts_geometry_and_page_field`, locate the
step table by its header before asserting the existing widths
`[720, 4140, 3450]`; the first document table is now the two-column metadata
table. Extend the heading-style loop through `("Heading 4", "3")`.

- [ ] **Step 2: Run the Word export test and verify it fails on the old structure**

Run:

```bash
cd backend
conda run -n test-case-generate python tests/test_word_report_export.py
```

Expected: FAIL because the current document lacks the three chapters, summary tables, and Heading 4 detail level.

- [ ] **Step 3: Replace the tracked default shell template**

Copy the approved binary shell without changing its formatting:

```bash
cp backend/template/test_case_report-v2.docx backend/template/test_case_report.docx
```

Do not delete or stage `backend/template/test_case_report-v2.docx`; it is a user-owned source asset. The tracked `test_case_report.docx` remains the registry target, so `default` changes in place without adding a second public template identifier.

- [ ] **Step 4: Reduce the renderer to orchestration**

Keep `ReportRenderError`, template preparation, and field-update handling in `renderer.py`. Import the new objects and set the default section strategy list:

```python
class WordReportRenderer:
    def __init__(self, sections=None):
        self._sections = tuple(
            sections
            or (
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
            rendered_path = self._render_shell(
                context,
                template,
                temp_dir,
            )
            document = Document(rendered_path)
            anchor = self._find_anchor(document)
            composer = WordDocumentComposer(document, anchor)
            self._format_cover_title(document, context["metadata"]["document_name"])
            for section in self._sections:
                section.render(composer, context)
            anchor._element.getparent().remove(anchor._element)
            enable_field_updates(document)
            document.core_properties.title = context["metadata"]["document_name"]
            document.save(output_path)
```

Prepare the shell with `{{ document_title }}` instead of `{{ project_title }}`, and render:

```python
doc_template.render(
    {
        "document_title": context["metadata"]["document_name"],
        "body_anchor": BODY_ANCHOR,
    },
    autoescape=True,
)
```

Delete the old `_populate_body` and all low-level formatting duplicated by `document.py`.

- [ ] **Step 5: Update the route to use the builder object**

In `backend/app/routes/testcases.py`, replace the removed function import and call:

```python
from app.reports.context_builder import ReportContextBuilder

# ...
context = ReportContextBuilder().build(source)
```

Keep response MIME type, download behavior, cleanup, error mapping, and filename unchanged.

- [ ] **Step 6: Run the focused Word tests and make them pass**

Run:

```bash
cd backend
conda run -n test-case-generate python tests/test_report_context.py
conda run -n test-case-generate python tests/test_word_sections.py
conda run -n test-case-generate python tests/test_word_report_export.py
```

Expected: all focused tests report OK.

- [ ] **Step 7: Commit the default-template integration**

```bash
git add backend/app/reports/renderer.py backend/app/routes/testcases.py backend/template/test_case_report.docx backend/tests/test_word_report_export.py
git commit -m "feat: 切换默认 Word 测试用例模板"
```

---

### Task 4: Run Full Regression and Structural Verification

**Files:**

- Verify only; modify the files from Tasks 1–3 only if a real regression is found.

**Interfaces:**

- Verifies the public export endpoint and all backend services as an integrated system.

- [ ] **Step 1: Run syntax compilation**

Run:

```bash
conda run -n test-case-generate python -m compileall -q backend/app backend/tests
```

Expected: exit code 0 and no output.

- [ ] **Step 2: Run the complete backend test suite**

Run:

```bash
cd backend
conda run -n test-case-generate python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: exit code 0, all tests OK, no failures or errors.

- [ ] **Step 3: Inspect the final generated document package**

Generate the document through the API test fixture and inspect the saved response with `python-docx`. Verify these literal behaviors in the test output:

- Core title is `Flight 2026飞控项目测试用例文档`.
- There are exactly three Heading 1 chapter paragraphs.
- Module/requirement/test-case paragraphs use Heading 2/3/4.
- The requirement-statistics module cell spans both requirements in `登录 Module 1`.
- Type counts are `功能测试 = 2`; priorities are `P0 = 1` and `P1 = 1`.
- `REQ-EMPTY` has zero cases and status `未覆盖`.
- The footer XML still contains `PAGE`, and the document still has two sections.

If any literal check is not already asserted by `test_word_report_export.py`, add the assertion, first demonstrate that it fails under the incorrect behavior, then make the minimal production correction and rerun the focused test.

- [ ] **Step 4: Review the diff for scope and user-owned files**

Run:

```bash
git status --short
git diff --check
git diff --stat HEAD~3..HEAD
git diff --name-only HEAD~3..HEAD
```

Expected changed implementation paths are limited to:

- `backend/app/reports/context_builder.py`
- `backend/app/reports/document.py`
- `backend/app/reports/sections.py`
- `backend/app/reports/renderer.py`
- `backend/app/routes/testcases.py`
- `backend/template/test_case_report.docx`
- `backend/tests/test_report_context.py`
- `backend/tests/test_word_sections.py`
- `backend/tests/test_word_report_export.py`

The pre-existing untracked `backend/template/test_case_report-v2.docx` and `readme.md` must remain unstaged and unchanged.

- [ ] **Step 5: Apply the verification-before-completion gate**

Read the full output of the compile and complete test-suite commands. Only report completion if both fresh commands exit 0 and the structural assertions pass. Report exact test counts and any remaining unrelated working-tree changes.
