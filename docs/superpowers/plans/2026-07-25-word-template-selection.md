# Word Template Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every generated Word table use five-point Chinese size (`10.5 pt`), expose the available Word report templates through a backend API, and let users choose a template in the frontend export dialog.

**Architecture:** The backend template registry is the single source of truth for template code, display name, file name, and render markers. A dedicated read-only route exposes only existing templates as `{template_id, name}`; the frontend caches this catalog, expands the selected Word format card, and passes the chosen ID through the existing export request.

**Tech Stack:** Python 3.11, Flask 3.1.2, python-docx 1.2.0, unittest, Vue 3.5, TypeScript 5.9, Vite 5.4, Node 24 type stripping.

## Global Constraints

- The only current display name is `标准测试用例文档`.
- Table headers and table body text in every generated Word template use exactly `10.5 pt`.
- Template configuration stays hard-coded in one convenient ordered Python mapping.
- The template-list API does not expose server paths, filenames, title markers, or anchor strategies.
- Only registered templates whose files exist are returned to the frontend.
- The frontend displays template names only and passes the selected template code as the existing `template_id` query parameter.
- JSON, Markdown, and Excel export behavior remains unchanged.
- Preserve the user-owned untracked `backend/template/test_case_report-v2.docx` and `readme.md`.

---

## File Structure

- Modify `backend/app/reports/document.py`: add a table font-size token and apply it to every header/body cell run.
- Modify `backend/tests/test_word_sections.py`: assert that all generated table runs are `10.5 pt`.
- Modify `backend/app/reports/template_registry.py`: replace the nested dict with typed ordered definitions carrying the display name and add an existing-file catalog function.
- Create `backend/app/routes/report_templates.py`: expose the global read-only template catalog.
- Modify `backend/app/__init__.py`: register the new blueprint under `/v1`.
- Create `backend/tests/test_report_templates.py`: verify registry mapping, file filtering, response shape, order, and path secrecy.
- Modify `API.md`: document the new template-list endpoint and response.
- Modify `frontend/src/api/projects.ts`: type and fetch the template catalog; keep Word export parameterized by template ID.
- Create `frontend/src/composables/wordTemplateSelection.ts`: isolate deterministic selection/payload rules.
- Create `frontend/src/composables/wordTemplateSelection.test.ts`: run selection rules directly with Node 24.
- Modify `frontend/src/composables/useTestcaseExport.ts`: load/cache/retry the template catalog and export the chosen Word template.
- Modify `frontend/src/components/ExportTestcasesDialog.vue`: expand the Word card and render template loading/error/empty/selected states.
- Modify `frontend/src/views/TestCases.vue`: pass template state to the dialog.

---

### Task 1: Apply Five-Point Font Size to All Word Tables

**Files:**

- Modify: `backend/tests/test_word_sections.py`
- Modify: `backend/app/reports/document.py`

**Interfaces:**

- Produces: `TABLE_FONT_SIZE = 10.5`
- Preserves: `WordDocumentComposer.add_table(...)`
- Preserves: all existing paragraph and heading sizes outside tables.

- [ ] **Step 1: Add a failing behavior test for header and body cell font sizes**

Add this method to `WordSectionTest`. The production break it catches is a table formatter that falls back to the 12-point report-body size.

```python
def test_every_table_header_and_body_run_uses_five_point_size(self):
    for table in self.document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        self.assertEqual(run.font.size.pt, 10.5)
```

- [ ] **Step 2: Run the focused test and verify the expected failure**

Run:

```bash
cd backend
conda run -n test-case-generate python -m unittest discover \
  -s tests -p "test_word_sections.py" -v
```

Expected: FAIL with a literal `12.0 != 10.5` table-run size mismatch.

- [ ] **Step 3: Implement the table-only font token**

In `backend/app/reports/document.py`, add:

```python
TABLE_FONT_SIZE = 10.5
```

In `WordDocumentComposer._format_cell`, set the run size explicitly:

```python
run = paragraph.add_run(str(text))
set_run_font(run, size=TABLE_FONT_SIZE, bold=bold)
```

Do not change `BODY_SIZE`, heading sizes, or metadata paragraph sizes.

- [ ] **Step 4: Run the Word section and export regressions**

Run:

```bash
cd backend
conda run -n test-case-generate python -m unittest discover \
  -s tests -p "test_word_sections.py" -v
conda run -n test-case-generate python -m unittest discover \
  -s tests -p "test_word_report_export.py" -v
```

Expected: all section and export tests report OK.

- [ ] **Step 5: Commit the Word table font change**

```bash
git add backend/app/reports/document.py backend/tests/test_word_sections.py
git commit -m "style: 统一 Word 表格为五号字"
```

---

### Task 2: Expose the Available Word Template Catalog

**Files:**

- Modify: `backend/app/reports/template_registry.py`
- Create: `backend/app/routes/report_templates.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_report_templates.py`
- Modify: `API.md`

**Interfaces:**

- Produces: immutable `ReportTemplateDefinition`.
- Produces: `available_templates(base_dir: str) -> tuple[dict[str, str], ...]`.
- Preserves: `resolve_template(base_dir: str, template_id: str) -> ReportTemplate | None`.
- Produces: `GET /v1/testcase-report-templates`.

- [ ] **Step 1: Write failing registry and API tests**

Create `backend/tests/test_report_templates.py`. The tests use real filesystem fixtures and the real Flask application; they do not mock the registry.

```python
import os
import tempfile
import unittest
from unittest.mock import patch

from app.reports.template_registry import (
    available_templates,
    resolve_template,
)


class ReportTemplateRegistryTest(unittest.TestCase):
    def test_resolves_default_template_name_code_and_path(self):
        with tempfile.TemporaryDirectory() as base_dir:
            template_dir = os.path.join(base_dir, "template")
            os.makedirs(template_dir)
            template_path = os.path.join(
                template_dir,
                "test_case_report.docx",
            )
            open(template_path, "wb").close()

            template = resolve_template(base_dir, "default")

            self.assertEqual(template.template_id, "default")
            self.assertEqual(template.name, "标准测试用例文档")
            self.assertEqual(template.path, template_path)
            self.assertEqual(
                available_templates(base_dir),
                (
                    {
                        "template_id": "default",
                        "name": "标准测试用例文档",
                    },
                ),
            )

    def test_catalog_filters_registered_template_with_missing_file(self):
        with tempfile.TemporaryDirectory() as base_dir:
            os.makedirs(os.path.join(base_dir, "template"))

            self.assertEqual(available_templates(base_dir), ())


class ReportTemplateApiTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        environment = patch.dict(
            os.environ,
            {
                "DATA_DIR": self.tmpdir.name,
                "UNIPORTAL_SYNC_ENABLED": "false",
            },
            clear=False,
        )
        environment.start()
        self.addCleanup(environment.stop)

        from app import create_app

        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_lists_available_templates_without_server_path(self):
        response = self.client.get("/v1/testcase-report-templates")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(
            payload["data"]["list"],
            [
                {
                    "template_id": "default",
                    "name": "标准测试用例文档",
                }
            ],
        )
        self.assertNotIn("path", payload["data"]["list"][0])
        self.assertNotIn("filename", payload["data"]["list"][0])


if __name__ == "__main__":
    unittest.main()
```

Use `Path(template_path).touch()` in the implementation if the test style checker rejects bare `open`; production code must not create files.

- [ ] **Step 2: Run the template test and verify the expected failure**

Run:

```bash
cd backend
conda run -n test-case-generate python -m unittest discover \
  -s tests -p "test_report_templates.py" -v
```

Expected: FAIL because `available_templates` and `ReportTemplate.name` do not exist, and the API route is not registered.

- [ ] **Step 3: Implement the typed ordered registry**

Replace the anonymous nested mapping in `template_registry.py` with:

```python
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
    ),
}
```

Resolve and list through the same definition:

```python
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
```

Keep `registered_template_ids()` returning the ordered tuple of mapping keys.

- [ ] **Step 4: Implement and register the read-only route**

Create `backend/app/routes/report_templates.py`:

```python
from flask import Blueprint, current_app

from app.reports.template_registry import available_templates
from app.utils.responses import ok


report_templates_bp = Blueprint("report_templates", __name__)


@report_templates_bp.get("/testcase-report-templates")
def list_testcase_report_templates():
    config = current_app.config["APP_CONFIG"]
    return ok({"list": list(available_templates(config.base_dir))})
```

Register it in `backend/app/__init__.py`:

```python
from app.routes.report_templates import report_templates_bp

# inside create_app()
app.register_blueprint(report_templates_bp, url_prefix="/v1")
```

- [ ] **Step 5: Document the endpoint**

Add to `API.md`:

```markdown
### Word 报告模板

`GET /v1/testcase-report-templates`

返回当前注册且模板文件存在的 Word 报告模板：

```json
{"code":0,"message":"ok","data":{"list":[{"template_id":"default","name":"标准测试用例文档"}]}}
```

响应不包含服务器模板路径。Word 导出时把 `template_id` 作为现有
`GET /projects/{projectId}/testcases/export` 的查询参数。
```

- [ ] **Step 6: Run focused and full backend tests**

Run:

```bash
cd backend
conda run -n test-case-generate python -m unittest discover \
  -s tests -p "test_report_templates.py" -v
conda run -n test-case-generate python -m unittest discover \
  -s tests -p "test_word_report_export.py" -v
conda run -n test-case-generate python -m unittest discover \
  -s tests -p "test_*.py" -v
```

Expected: all tests report OK; the complete suite includes the new catalog tests.

- [ ] **Step 7: Commit the backend template catalog**

```bash
git add API.md backend/app/__init__.py backend/app/reports/template_registry.py backend/app/routes/report_templates.py backend/tests/test_report_templates.py
git commit -m "feat: 提供 Word 模板目录接口"
```

---

### Task 3: Add Frontend Word Template Selection

**Files:**

- Modify: `frontend/src/api/projects.ts`
- Create: `frontend/src/composables/wordTemplateSelection.ts`
- Create: `frontend/src/composables/wordTemplateSelection.test.ts`
- Modify: `frontend/src/composables/useTestcaseExport.ts`
- Modify: `frontend/src/components/ExportTestcasesDialog.vue`
- Modify: `frontend/src/views/TestCases.vue`

**Interfaces:**

- Produces: `WordReportTemplate = { template_id: string; name: string }`.
- Produces: `fetchWordReportTemplates() -> Promise<WordReportTemplate[]>`.
- Produces: `ExportSelection = { format: ExportFormat; templateId?: string }`.
- `ExportTestcasesDialog` consumes template list/loading/error props and emits `ExportSelection`.
- `useTestcaseExport.handleExport(selection)` passes the selected template ID to `exportTestcasesWord`.

- [ ] **Step 1: Write a failing pure TypeScript selection test**

Create `frontend/src/composables/wordTemplateSelection.test.ts`:

```typescript
import assert from 'node:assert/strict'
import {
  buildExportSelection,
  selectInitialTemplateId
} from './wordTemplateSelection.ts'

const templates = [
  { template_id: 'default', name: '标准测试用例文档' },
  { template_id: 'compact', name: '精简模板' }
]

assert.equal(selectInitialTemplateId(templates, ''), 'default')
assert.equal(
  selectInitialTemplateId(templates, 'compact'),
  'compact'
)
assert.equal(
  selectInitialTemplateId(templates, 'missing'),
  'default'
)
assert.deepEqual(
  buildExportSelection('word', 'default'),
  { format: 'word', templateId: 'default' }
)
assert.equal(buildExportSelection('word', ''), null)
assert.deepEqual(
  buildExportSelection('excel', ''),
  { format: 'excel' }
)
```

- [ ] **Step 2: Run the TypeScript test and verify the missing-module failure**

Run:

```bash
/Users/rcx/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  --experimental-strip-types \
  frontend/src/composables/wordTemplateSelection.test.ts
```

Expected: FAIL because `wordTemplateSelection.ts` does not exist.

- [ ] **Step 3: Implement the deterministic selection model**

Create `frontend/src/composables/wordTemplateSelection.ts`:

```typescript
import type { WordReportTemplate } from '../api/projects'

export type ExportFormat = 'json' | 'md' | 'word' | 'excel'

export type ExportSelection = {
  format: ExportFormat
  templateId?: string
}

export const selectInitialTemplateId = (
  templates: WordReportTemplate[],
  currentTemplateId: string
) => {
  if (templates.some((item) => item.template_id === currentTemplateId)) {
    return currentTemplateId
  }
  return templates[0]?.template_id ?? ''
}

export const buildExportSelection = (
  format: ExportFormat,
  templateId: string
): ExportSelection | null => {
  if (format === 'word') {
    return templateId
      ? { format, templateId }
      : null
  }
  return { format }
}
```

Run the Node test again. Expected: exit code 0 and no output.

- [ ] **Step 4: Add the typed catalog API client**

In `frontend/src/api/projects.ts` add:

```typescript
export type WordReportTemplate = {
  template_id: string
  name: string
}

type WordReportTemplateListResponse = {
  list: WordReportTemplate[]
}

const fetchWordReportTemplates = async () => {
  const response = await requestJson<WordReportTemplateListResponse>(
    '/testcase-report-templates'
  )
  return response.data.list ?? []
}
```

Export `fetchWordReportTemplates`. Keep
`exportTestcasesWord(projectId, templateId = "default")` unchanged.

- [ ] **Step 5: Load, cache, and retry the catalog in the export composable**

Update imports in `useTestcaseExport.ts`:

```typescript
import {
  exportTestcasesExcel,
  exportTestcasesWord,
  fetchWordReportTemplates,
  type WordReportTemplate
} from '../api/projects'
import type {
  ExportSelection
} from './wordTemplateSelection'
```

Add state and a guarded loader:

```typescript
const wordTemplates = ref<WordReportTemplate[]>([])
const wordTemplatesLoading = ref(false)
const wordTemplatesError = ref('')

const loadWordTemplates = async () => {
  if (wordTemplatesLoading.value || wordTemplates.value.length > 0) {
    return
  }
  wordTemplatesLoading.value = true
  wordTemplatesError.value = ''
  try {
    wordTemplates.value = await fetchWordReportTemplates()
  } catch {
    wordTemplatesError.value = '模板加载失败，请重新打开弹窗重试'
  } finally {
    wordTemplatesLoading.value = false
  }
}

const openExportDialog = () => {
  exportDialogVisible.value = true
  void loadWordTemplates()
}
```

Change the handler:

```typescript
const handleExport = async (selection: ExportSelection) => {
  const { format, templateId } = selection
  // existing JSON/Markdown branches stay unchanged
  if (format === 'word') {
    if (!templateId) {
      return
    }
    const { blob, headers } = await exportTestcasesWord(
      projectId.value,
      templateId
    )
    triggerBlobDownload(blob, headers, `${baseName}-测试报告.docx`)
    return
  }
  // existing Excel branch stays unchanged
}
```

Return `wordTemplates`, `wordTemplatesLoading`, and `wordTemplatesError`.

- [ ] **Step 6: Expand the Word card and emit the selection object**

In `ExportTestcasesDialog.vue`:

- Import `selectInitialTemplateId`, `buildExportSelection`, and their types.
- Add props:

```typescript
wordTemplates: WordReportTemplate[]
wordTemplatesLoading: boolean
wordTemplatesError: string
```

- Change the event:

```typescript
(event: 'export', value: ExportSelection): void
```

- Add `selectedTemplateId = ref('')`.
- Watch template props and dialog opening through `selectInitialTemplateId`.
- Wrap each format in a bordered container. Keep the existing format button as its top row.
- When `item.value === "word"` and Word is selected, append a bordered inner area:

```vue
<div
  v-if="item.value === 'word' && selectedFormat === 'word'"
  class="border-t border-zinc-200 px-4 py-3"
>
  <p v-if="wordTemplatesLoading" class="text-xs text-zinc-500">
    正在加载模板
  </p>
  <p v-else-if="wordTemplatesError" class="text-xs text-red-600">
    {{ wordTemplatesError }}
  </p>
  <p v-else-if="wordTemplates.length === 0" class="text-xs text-zinc-500">
    暂无可用模板
  </p>
  <button
    v-for="template in wordTemplates"
    v-else
    :key="template.template_id"
    type="button"
    class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm"
    :class="selectedTemplateId === template.template_id
      ? 'bg-zinc-100 text-zinc-950'
      : 'text-zinc-600 hover:bg-zinc-50'"
    @click="selectedTemplateId = template.template_id"
  >
    <span
      class="h-2.5 w-2.5 rounded-full"
      :class="selectedTemplateId === template.template_id
        ? 'bg-zinc-950'
        : 'bg-zinc-200'"
    ></span>
    {{ template.name }}
  </button>
</div>
```

Vue does not permit `v-else` and `v-for` on the same element reliably; implement the final version with a `<template v-else>` wrapper around the template buttons.

Disable the footer action when Word lacks a valid template:

```vue
<AppDialogButton
  variant="primary"
  :disabled="selectedFormat === 'word' && (
    wordTemplatesLoading
    || Boolean(wordTemplatesError)
    || !selectedTemplateId
  )"
  @click="confirmExport"
>
  导出
</AppDialogButton>
```

Build the payload and return without emitting if it is null.

- [ ] **Step 7: Pass the catalog state from the page**

In `TestCases.vue`, destructure the new composable values and pass:

```vue
<ExportTestcasesDialog
  v-model="exportDialogVisible"
  :word-templates="wordTemplates"
  :word-templates-loading="wordTemplatesLoading"
  :word-templates-error="wordTemplatesError"
  @export="handleExport"
/>
```

- [ ] **Step 8: Run frontend logic and production build verification**

Run:

```bash
/Users/rcx/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  --experimental-strip-types \
  frontend/src/composables/wordTemplateSelection.test.ts
cd frontend
npm run build
```

Expected: the logic test exits 0; `vue-tsc -b` and `vite build` both succeed.

- [ ] **Step 9: Commit the frontend template selection**

```bash
git add frontend/src/api/projects.ts frontend/src/components/ExportTestcasesDialog.vue frontend/src/composables/useTestcaseExport.ts frontend/src/composables/wordTemplateSelection.ts frontend/src/composables/wordTemplateSelection.test.ts frontend/src/views/TestCases.vue
git commit -m "feat: 支持选择 Word 导出模板"
```

---

### Task 4: Complete Full Regression and Visual Verification

**Files:**

- Verify all files from Tasks 1–3; modify only when verification reveals a real defect.

- [ ] **Step 1: Run fresh backend compilation and full tests**

Run from the repository root:

```bash
conda run -n test-case-generate python -m compileall -q backend/app backend/tests
cd backend
conda run -n test-case-generate python -m unittest discover \
  -s tests -p "test_*.py" -v
```

Expected: compile exit code 0 with no output; the complete suite reports OK.

- [ ] **Step 2: Run fresh frontend verification**

Run:

```bash
/Users/rcx/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  --experimental-strip-types \
  frontend/src/composables/wordTemplateSelection.test.ts
cd frontend
npm run build
```

Expected: both commands exit 0.

- [ ] **Step 3: Render and inspect a representative multi-page Word**

Generate a report containing:

- two requirements in one merged module,
- one requirement in a second module,
- covered and uncovered requirements,
- two case types and two priorities,
- a multi-row step table.

Render with the packaged document renderer and a fontconfig alias mapping
`宋体` to an installed Chinese font. Use `--emit_pdf`, confirm the PDF and PNG
page counts agree, and inspect every page at 100% zoom. Verify:

- cover title is isolated and readable,
- all three chapters are present,
- table text is visually smaller than 12-point body text and structurally `10.5 pt`,
- merged module cells, wrapping, repeated headers, borders, and page breaks are clean,
- all detail content reaches the final page,
- footer page numbers remain present.

- [ ] **Step 4: Review scope and user-owned files**

Run:

```bash
git status --short
git diff --check
git log -8 --oneline
```

Confirm `backend/template/test_case_report-v2.docx` and `readme.md` remain
untracked and unstaged. Confirm no unrelated frontend or backend file changed.

- [ ] **Step 5: Apply completion gate**

Only report completion after fresh backend tests, frontend logic test, frontend
build, and all-page Word visual QA pass. Report exact test counts and explicitly
name any pre-existing untracked files.
