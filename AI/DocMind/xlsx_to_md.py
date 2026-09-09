import re
import sys
from pathlib import Path
import openpyxl

# Heading-like single-cell lines: numbered sections, bracketed labels, circled numbers.
HEADING_START = re.compile(
    r"^\s*(\(?\d+(\.\d+)*\.?\)?[-)]?\s|[①-⑳⓪]\s|\[[^\]]+\]\s?)"
)
# Bare number, e.g. empty table skeleton rows that only hold a sequence "1 2 3 ...".
BARE_NUMBER = re.compile(r"^\d+$")
# Skip the repeated document-metadata block (every sheet has it as first rows).
META_CELLS = {"ドキュメントID", "ドキュメント名称", "作成日", "更新日", "更新者", "バージョン"}


def cell_text(v):
    if v is None:
        return ""
    s = str(v).strip()
    if not s:
        return ""
    return s.replace("|", "\\|")


def norm(rows):
    """Return list of rows, each a list of (col_idx_1based, value)."""
    out = []
    for row in rows:
        cells = []
        for c, v in enumerate(row, start=1):
            t = cell_text(v)
            if t:
                cells.append((c, t))
        out.append(cells)
    return out


def is_meta_block(cells_list):
    if len(cells_list) < 2:
        return False
    first = {v for _, v in cells_list[0]}
    return META_CELLS.issubset(first)


def blockify(cells_list):
    """Group rows into table blocks and text blocks.

    A table block may span blank (empty) separator rows provided the
    surrounding rows share a compatible column signature.  A real
    single-cell (text) row always closes a table block.
    """
    blocks = []
    i = 0
    n = len(cells_list)
    while i < n:
        cells = cells_list[i]
        if len(cells) >= 2:
            j = i
            union = {c for c, _ in cells}
            while j < n:
                row = cells_list[j]
                lr = len(row)
                if lr >= 2:
                    union |= {c for c, _ in row}
                    j += 1
                elif lr == 0:
                    k = j
                    while k < n and len(cells_list[k]) == 0:
                        k += 1
                    if (
                        k < n
                        and len(cells_list[k]) >= 2
                        and (union & {c for c, _ in cells_list[k]})
                    ):
                        union |= {c for c, _ in cells_list[k]}
                        j = k + 1
                    else:
                        break
                else:
                    break
            blocks.append(("table", cells_list[i:j]))
            i = j
        else:
            j = i
            while j < n and len(cells_list[j]) < 2:
                j += 1
            blocks.append(("text", cells_list[i:j]))
            i = j
    return blocks


TREE_GLYPH = ("└", "┌", "├", "│", "─", "┬", "┴")


def is_tree_row(cells):
    vals = [v.strip() for _, v in cells]
    if not vals:
        return False
    named = [v for v in vals if v and v not in TREE_GLYPH]
    tree = [v for v in vals if v in TREE_GLYPH]
    return bool(tree) and bool(named)


def render_table(cells_list):
    # Skip any block that is the repeated document-metadata header.
    if is_meta_block(cells_list):
        return None
    # Filter rows that are genuinely multi-cell (e.g. all-empty or single cell shouldn't be here,
    # but guard anyway).
    usable = [r for r in cells_list if len(r) >= 1]
    if not usable:
        return None
    # Union of used columns, kept in ascending order.
    cols = sorted({c for r in usable for c, _ in r})
    # Drop leading/trailing columns that are empty across ALL rows (layout-only).
    def col_used(c):
        return any(c == cc for r in usable for cc, _ in r)

    while cols and not col_used(cols[0]):
        cols.pop(0)
    while cols and not col_used(cols[-1]):
        cols.pop()
    if not cols:
        return None

    # File/directory tree rows are rendered as indented text lines instead of a
    # sparse markdown table.
    if any(is_tree_row(r) for r in usable) and len(cols) >= 2:
        return render_tree(usable)
    # First row = header.
    header = {c: v for c, v in usable[0]}
    lines = ["| " + " | ".join(header.get(c, "") for c in cols) + " |"]
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for r in usable[1:]:
        m = {c: v for c, v in r}
        lines.append("| " + " | ".join(m.get(c, "") for c in cols) + " |")
    return "\n".join(lines)


def render_tree(cells_list):
    """Render a file/directory tree as indented text lines.

    The leading tree-glyph cell (e.g. '└') at varying columns carries depth;
    the cell right after it is the node name and the last column is a
    description.
    """
    rows = [r for r in cells_list if r]
    if not rows:
        return None
    base = min(c for r in rows for c, _ in r)
    lines = []
    for cells in rows:
        sorted_cells = sorted(cells)
        glyph_col = next((c for c, v in sorted_cells if v in TREE_GLYPH), sorted_cells[0][0])
        glyph = next((v for c, v in sorted_cells if v in TREE_GLYPH), "•")
        name = ""
        desc = ""
        for c, v in sorted_cells:
            if c <= glyph_col or v in TREE_GLYPH:
                continue
            if not name:
                name = v
            else:
                desc = v
        line = "  " * (glyph_col - base) + f"{glyph} {name}"
        if desc:
            line += f" — {desc}"
        lines.append(line)
    return "\n".join(lines)


def render_text(cells_list):
    lines = []
    # Group consecutive single-cell rows that share the same column into one paragraph.
    j = 0
    while j < len(cells_list):
        c, v = cells_list[j][0] if cells_list[j] else (None, "")
        if not v:
            j += 1
            continue
        if BARE_NUMBER.match(v):
            j += 1
            continue
        if HEADING_START.match(v):
            # Determine heading level by column depth (A-deepest).
            level = max(2, min(6, c + 1))
            lines.append(f"{'#' * level} {v}")
            j += 1
            continue
        # Body paragraph: join consecutive rows sharing this column.
        buf = [v]
        k = j + 1
        while k < len(cells_list) and len(cells_list[k]) == 1:
            c2, v2 = cells_list[k][0]
            if c2 == c:
                buf.append(v2)
                k += 1
            else:
                break
        lines.append(" ".join(buf))
        j = k
    return "\n\n".join(lines)


def sheet_to_md(ws):
    raw = list(ws.iter_rows(values_only=True))
    rows = norm(raw)
    blocks = blockify(rows)
    out = []
    for kind, cells_list in blocks:
        if kind == "table":
            t = render_table(cells_list)
            if t:
                out.append(t)
        else:
            t = render_text(cells_list)
            if t:
                out.append(t)
    return "\n\n".join(out)


def xlsx_to_md(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    parts = []
    for name in wb.sheetnames:
        body = sheet_to_md(wb[name])
        if not body:
            continue
        parts.append(f"# {name}\n\n{body}")
    return "\n\n".join(parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python xlsx_to_md.py <file.xlsx> [output.md]")
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".md")
    dst.write_text(xlsx_to_md(src), encoding="utf-8")
    print(f"Saved to {dst}")


if __name__ == "__main__":
    main()
