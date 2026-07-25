from abc import ABC, abstractmethod


REQUIREMENT_WIDTHS = (1500, 1300, 2300, 1600, 1610)
STATISTIC_WIDTHS = (3500, 1800, 3010)
COVERAGE_WIDTHS = (1300, 1800, 3000, 1000, 1210)


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
        summary = context["summary"]
        composer.add_heading("二、需求与用例概述", 1)
        self._render_requirement_stats(composer, summary)
        self._render_case_stats(composer, summary)
        self._render_coverage(composer, summary)

    @staticmethod
    def _render_requirement_stats(composer, summary):
        composer.add_heading("需求统计", 2)
        rows = []
        merge_ranges = []
        for group in summary["requirement_groups"]:
            first_row = len(rows)
            for requirement_index, requirement in enumerate(
                group["requirements"]
            ):
                rows.append(
                    (
                        group["module"] if requirement_index == 0 else "",
                        requirement["code"],
                        requirement["title"],
                        requirement["type"],
                        requirement["testcase_count"],
                    )
                )
            last_row = len(rows) - 1
            if first_row < last_row:
                merge_ranges.append((0, first_row, last_row))
        if not rows:
            rows.append(("暂无数据", "", "", "", ""))
        composer.add_table(
            ("模块", "需求编号", "需求名称", "需求类型", "用例数量"),
            rows,
            REQUIREMENT_WIDTHS,
            centered_columns=(0, 1, 4),
            merge_ranges=merge_ranges,
        )

    @classmethod
    def _render_case_stats(cls, composer, summary):
        composer.add_heading("用例统计", 2)
        composer.add_heading("按用例类型统计", 3)
        composer.add_table(
            ("用例类型", "用例数量", "占比"),
            cls._statistic_rows(summary["case_type_stats"]),
            STATISTIC_WIDTHS,
            centered_columns=(1, 2),
        )
        composer.add_heading("按优先级统计", 3)
        composer.add_table(
            ("优先级", "用例数量", "占比"),
            cls._statistic_rows(summary["priority_stats"]),
            STATISTIC_WIDTHS,
            centered_columns=(0, 1, 2),
        )

    @staticmethod
    def _statistic_rows(statistics):
        if not statistics:
            return (("暂无数据", "", ""),)
        return tuple(
            (item["name"], item["count"], item["percentage"])
            for item in statistics
        )

    @staticmethod
    def _render_coverage(composer, summary):
        composer.add_heading("需求覆盖分析", 2)
        rows = [
            (
                item["code"],
                item["title"],
                item["testcase_codes"],
                item["testcase_count"],
                item["status"],
            )
            for item in summary["coverage"]
        ]
        if not rows:
            rows.append(("暂无数据", "", "", "", ""))
        composer.add_table(
            ("需求编号", "需求名称", "关联用例", "用例数量", "覆盖状态"),
            rows,
            COVERAGE_WIDTHS,
            centered_columns=(0, 3, 4),
        )


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

    @staticmethod
    def _render_testcases(composer, testcases):
        if not testcases:
            composer.add_metadata("测试用例", "暂无")
            return

        for case_index, testcase in enumerate(testcases, start=1):
            composer.add_heading(
                f"{case_index}. {testcase['title']}",
                4,
            )
            composer.add_metadata("编号", testcase["code"])
            composer.add_metadata("类型", testcase["type"])
            composer.add_metadata("场景", testcase["scenario_type"])
            composer.add_metadata("优先级", testcase["priority"])
            composer.add_metadata(
                "测试目标",
                testcase["test_target_desc"],
            )
            composer.add_metadata("验证方法", testcase["verify_method"])
            if testcase["steps"]:
                composer.add_label("测试步骤")
                composer.add_steps_table(testcase["steps"])
            else:
                composer.add_metadata("测试步骤", "暂无")
