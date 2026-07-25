from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


CHINESE_FONT = "宋体"
LATIN_FONT = "Times New Roman"
BODY_SIZE = 12
TABLE_INDENT = 120
TABLE_COLOR = "A6A6A6"
HEADER_FILL = "D9EAF7"


def set_font(element, size=BODY_SIZE, bold=None):
    element.font.name = LATIN_FONT
    element.font.size = Pt(size)
    if bold is not None:
        element.font.bold = bold
    run_properties = element._element.get_or_add_rPr()
    fonts = run_properties.get_or_add_rFonts()
    fonts.set(qn("w:ascii"), LATIN_FONT)
    fonts.set(qn("w:hAnsi"), LATIN_FONT)
    fonts.set(qn("w:cs"), LATIN_FONT)
    fonts.set(qn("w:eastAsia"), CHINESE_FONT)


def set_run_font(run, size=BODY_SIZE, bold=None):
    run.font.name = LATIN_FONT
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run_properties = run._element.get_or_add_rPr()
    fonts = run_properties.get_or_add_rFonts()
    fonts.set(qn("w:ascii"), LATIN_FONT)
    fonts.set(qn("w:hAnsi"), LATIN_FONT)
    fonts.set(qn("w:cs"), LATIN_FONT)
    fonts.set(qn("w:eastAsia"), CHINESE_FONT)


def _clear_paragraph(paragraph):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def _get_or_create_style(
    document,
    name,
    size,
    bold,
    before,
    after,
    line_spacing=1.5,
):
    try:
        style = document.styles[name]
    except KeyError:
        style = document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    set_font(style, size=size, bold=bold)
    style.paragraph_format.space_before = Pt(before)
    style.paragraph_format.space_after = Pt(after)
    style.paragraph_format.line_spacing = line_spacing
    return style


def _configure_heading_style(style, size, before, after, outline_level):
    set_font(style, size=size, bold=True)
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


def configure_styles(document):
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
    _configure_heading_style(document.styles["Heading 4"], 12, 6, 4, 3)


def _set_cell_margins(cell, top=120, start=120, bottom=120, end=120):
    cell_properties = cell._tc.get_or_add_tcPr()
    margins = cell_properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        cell_properties.append(margins)
    for name, value in (
        ("top", top),
        ("start", start),
        ("bottom", bottom),
        ("end", end),
    ):
        node = margins.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _set_cell_width(cell, width):
    cell_properties = cell._tc.get_or_add_tcPr()
    cell_width = cell_properties.first_child_found_in("w:tcW")
    if cell_width is None:
        cell_width = OxmlElement("w:tcW")
        cell_properties.append(cell_width)
    cell_width.set(qn("w:w"), str(width))
    cell_width.set(qn("w:type"), "dxa")


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

    def add_body(self, text):
        return self._add_paragraph(text, "Report Body")

    def add_label(self, text):
        return self._add_paragraph(
            text,
            "Report Step Label",
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
        headers = tuple(headers)
        rows = tuple(rows)
        widths = tuple(widths)
        if len(widths) != len(headers):
            raise ValueError("表格列宽数量必须与表头数量一致")
        if any(len(row) != len(headers) for row in rows):
            raise ValueError("表格数据列数必须与表头数量一致")

        table = self.document.add_table(
            rows=1 + len(rows),
            cols=len(headers),
        )
        for column_index, header in enumerate(headers):
            self._format_cell(
                table.rows[0].cells[column_index],
                header,
                bold=True,
                centered=True,
                fill=HEADER_FILL,
            )
        header_properties = table.rows[0]._tr.get_or_add_trPr()
        header_properties.append(OxmlElement("w:tblHeader"))

        centered_columns = frozenset(centered_columns)
        for row_index, values in enumerate(rows, start=1):
            for column_index, value in enumerate(values):
                self._format_cell(
                    table.rows[row_index].cells[column_index],
                    value,
                    centered=column_index in centered_columns,
                )

        self._set_table_geometry(table, widths)
        for column, first_body_row, last_body_row in merge_ranges:
            if first_body_row < last_body_row:
                merged_cell = table.cell(first_body_row + 1, column).merge(
                    table.cell(last_body_row + 1, column)
                )
                merged_cell.text = ""
                self._format_cell(
                    merged_cell,
                    rows[first_body_row][column],
                    centered=column in centered_columns,
                )

        self.anchor._p.addprevious(table._tbl)
        spacer = self.anchor.insert_paragraph_before(style="Report Body")
        spacer.paragraph_format.space_after = Pt(2)
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

    def _add_paragraph(
        self,
        text,
        style,
        keep_with_next=False,
    ):
        paragraph = self.anchor.insert_paragraph_before(style=style)
        run = paragraph.add_run(str(text))
        size = (
            paragraph.style.font.size.pt
            if paragraph.style.font.size
            else BODY_SIZE
        )
        set_run_font(run, size=size)
        paragraph.paragraph_format.keep_with_next = keep_with_next
        return paragraph

    @staticmethod
    def _format_cell(
        cell,
        text,
        bold=False,
        centered=False,
        fill=None,
    ):
        paragraph = cell.paragraphs[0]
        _clear_paragraph(paragraph)
        paragraph.style = "Report Body"
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.25
        paragraph.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
            if centered
            else WD_ALIGN_PARAGRAPH.LEFT
        )
        run = paragraph.add_run(str(text))
        set_run_font(run, bold=bold)
        if fill:
            cell_properties = cell._tc.get_or_add_tcPr()
            shading = cell_properties.first_child_found_in("w:shd")
            if shading is None:
                shading = OxmlElement("w:shd")
                cell_properties.append(shading)
            shading.set(qn("w:fill"), fill)

    @staticmethod
    def _set_table_geometry(table, widths):
        table.autofit = False
        table_properties = table._tbl.tblPr
        table_width = table_properties.first_child_found_in("w:tblW")
        table_width.set(qn("w:w"), str(sum(widths)))
        table_width.set(qn("w:type"), "dxa")

        layout = table_properties.first_child_found_in("w:tblLayout")
        if layout is None:
            layout = OxmlElement("w:tblLayout")
            table_properties.append(layout)
        layout.set(qn("w:type"), "fixed")

        indent = table_properties.first_child_found_in("w:tblInd")
        if indent is None:
            indent = OxmlElement("w:tblInd")
            table_properties.append(indent)
        indent.set(qn("w:w"), str(TABLE_INDENT))
        indent.set(qn("w:type"), "dxa")

        for grid_column, width in zip(table._tbl.tblGrid, widths):
            grid_column.set(qn("w:w"), str(width))

        borders = table_properties.first_child_found_in("w:tblBorders")
        if borders is None:
            borders = OxmlElement("w:tblBorders")
            table_properties.append(borders)
        for edge in (
            "top",
            "left",
            "bottom",
            "right",
            "insideH",
            "insideV",
        ):
            node = borders.find(qn(f"w:{edge}"))
            if node is None:
                node = OxmlElement(f"w:{edge}")
                borders.append(node)
            node.set(qn("w:val"), "single")
            node.set(qn("w:sz"), "4")
            node.set(qn("w:space"), "0")
            node.set(qn("w:color"), TABLE_COLOR)

        for row in table.rows:
            row_properties = row._tr.get_or_add_trPr()
            if row_properties.find(qn("w:cantSplit")) is None:
                row_properties.append(OxmlElement("w:cantSplit"))
            for cell, width in zip(row.cells, widths):
                _set_cell_width(cell, width)
                _set_cell_margins(cell)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
