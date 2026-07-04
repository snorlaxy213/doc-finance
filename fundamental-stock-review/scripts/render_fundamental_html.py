#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "assets" / "fundamental_report_template.html"


@dataclass
class TableBlock:
    heading: str
    headers: list[str]
    rows: list[list[str]]


@dataclass
class RenderedContent:
    html: str
    toc: list[tuple[str, str, str]]


def strip_md(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`]+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", strip_md(text)).strip()


def inline_md(text: str) -> str:
    escaped = html.escape(text.strip())
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda m: (
            f'<a href="{m.group(2)}" target="_blank" rel="noopener">'
            f"{m.group(1)}</a>"
        ),
        escaped,
    )
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    return escaped


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def is_table_start(lines: list[str], i: int) -> bool:
    if i + 1 >= len(lines):
        return False
    if not lines[i].lstrip().startswith("|"):
        return False
    return bool(re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[i + 1]))


def table_to_html(headers: list[str], rows: list[list[str]]) -> str:
    out: list[str] = ['<div class="tbl-scroll">', "<table>"]
    out.append("<thead><tr>")
    for head in headers:
        out.append(f'<th scope="col">{inline_md(head)}</th>')
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in rows:
        cells = row + [""] * (len(headers) - len(row))
        out.append("<tr>")
        for idx, cell in enumerate(cells[: len(headers)]):
            cls = value_class(cell)
            attr = f' class="{cls}"' if cls else ""
            if idx == 0:
                out.append(f'<th scope="row">{inline_md(cell)}</th>')
            else:
                out.append(f"<td{attr}>{inline_md(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def value_class(cell: str) -> str:
    raw = normalize_space(cell)
    if raw in {"未披露", "不适用", "无法判断", "无"}:
        return "muted"
    negative_terms = ("为负", "转负", "下滑", "下降", "亏损", "风险", "恶化", "偏高", "压力", "快于收入")
    if raw.startswith("-") or any(term in raw for term in negative_terms):
        return "down"
    positive_terms = ("增长", "改善", "提升", "转正", "修复", "上升", "强", "优秀", "良好")
    if raw.startswith("+") or any(term in raw for term in positive_terms):
        return "up"
    return ""


def heading_id(index: int) -> str:
    return f"s{index}"


def render_markdown(markdown: str) -> RenderedContent:
    lines = markdown.splitlines()
    out: list[str] = []
    toc: list[tuple[str, str, str]] = []
    section_open = False
    section_index = 0
    list_stack: list[tuple[int, str]] = []

    def close_lists() -> None:
        while list_stack:
            _, tag = list_stack.pop()
            out.append(f"</{tag}>")

    def close_section() -> None:
        nonlocal section_open
        close_lists()
        if section_open:
            out.append("</section>")
            section_open = False

    def open_or_adjust_list(indent: int, tag: str) -> None:
        while list_stack and indent < list_stack[-1][0]:
            _, old = list_stack.pop()
            out.append(f"</{old}>")
        if not list_stack or indent > list_stack[-1][0] or tag != list_stack[-1][1]:
            list_stack.append((indent, tag))
            out.append(f"<{tag}>")

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            close_lists()
            i += 1
            continue

        if stripped.startswith("```"):
            close_lists()
            lang = stripped.strip("`").strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            block_text = "\n".join(code_lines)
            if "基本面速记" in block_text or ("公司:" in block_text and "结论:" in block_text):
                i += 1
                continue
            language_attr = f' class="language-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{language_attr}>{html.escape(block_text)}</code></pre>")
            i += 1
            continue

        if is_table_start(lines, i):
            close_lists()
            headers = split_table_row(lines[i])
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(split_table_row(lines[i]))
                i += 1
            out.append(table_to_html(headers, rows))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading:
            close_lists()
            level = len(heading.group(1))
            text = strip_md(heading.group(2))
            if level <= 1:
                i += 1
                continue
            if level <= 3:
                close_section()
                section_index += 1
                sid = heading_id(section_index)
                num = extract_section_num(text, section_index)
                title = remove_section_num(text)
                toc.append((sid, f"{num:02d}" if isinstance(num, int) else str(num), title))
                out.append(f'<section id="{sid}">')
                out.append(
                    f'<h2 class="sec"><span class="num">{html.escape(str(num).zfill(2) if isinstance(num, int) else str(num))}</span>{inline_md(title)}</h2>'
                )
                section_open = True
            else:
                out.append(f'<h3 class="sub">{inline_md(text)}</h3>')
            i += 1
            continue

        list_match = re.match(r"^(\s*)([-+*]|\d+[.])\s+(.+)$", line)
        if list_match:
            indent = len(list_match.group(1).replace("\t", "    "))
            marker = list_match.group(2)
            tag = "ol" if marker[0].isdigit() else "ul"
            open_or_adjust_list(indent, tag)
            out.append(f"<li>{inline_md(list_match.group(3))}</li>")
            i += 1
            continue

        close_lists()
        paragraph_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith("#") or nxt.startswith("```") or is_table_start(lines, i):
                break
            if re.match(r"^(\s*)([-+*]|\d+[.])\s+(.+)$", lines[i]):
                break
            paragraph_lines.append(nxt)
            i += 1
        paragraph = " ".join(paragraph_lines)
        bold_title = re.match(r"^\*\*([^*：:]+)[：:]?\*\*$", paragraph)
        if bold_title:
            out.append(f'<h3 class="sub">{inline_md(bold_title.group(1))}</h3>')
        elif paragraph.startswith("**") and paragraph.endswith(":**"):
            out.append(f'<h3 class="sub">{inline_md(paragraph.strip("*:："))}</h3>')
        else:
            out.append(f"<p>{inline_md(paragraph)}</p>")

    close_section()
    return RenderedContent("\n".join(out), toc)


def extract_section_num(text: str, fallback: int) -> int | str:
    match = re.match(r"^(\d+)[.、\s]+", text)
    if match:
        return int(match.group(1))
    if "速记" in text or "结论" in text:
        return "◎"
    return fallback


def remove_section_num(text: str) -> str:
    return re.sub(r"^\d+[.、\s]+", "", text).strip()


def collect_tables(markdown: str) -> list[TableBlock]:
    lines = markdown.splitlines()
    tables: list[TableBlock] = []
    heading = ""
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        h = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if h:
            heading = strip_md(h.group(2))
        if is_table_start(lines, i):
            headers = split_table_row(lines[i])
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(split_table_row(lines[i]))
                i += 1
            tables.append(TableBlock(heading=heading, headers=headers, rows=rows))
            continue
        i += 1
    return tables


def extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return strip_md(line[2:])
    return "基本面分析报告"


def extract_company_and_ticker(title: str, markdown: str, company: str | None, ticker: str | None) -> tuple[str, str]:
    if not company:
        note_company = re.search(r"公司[：:]\s*([^\n（(]+)", markdown)
        if note_company:
            company = normalize_space(note_company.group(1))
    if not ticker:
        ticker_match = re.search(r"(\d{6})(?:\.(SZ|SH|BJ))?", title + "\n" + markdown)
        if ticker_match:
            suffix = ticker_match.group(2)
            ticker = ticker_match.group(1) + (f".{suffix}" if suffix else "")
    if not company:
        company = re.sub(r"\([^)]*\)", "", title)
        company = re.sub(r"(财报|基本面|综述|分析|报告|与估值)+", "", company).strip(" -_·")
    if not ticker:
        ticker = "未识别代码"
    return company or "未识别公司", ticker


def exchange_from_ticker(ticker: str) -> str:
    if ticker.endswith(".SZ"):
        return "深圳证券交易所"
    if ticker.endswith(".SH"):
        return "上海证券交易所"
    if ticker.endswith(".BJ"):
        return "北京证券交易所"
    return "交易所未识别"


def find_section(markdown: str, section_keyword: str) -> str:
    pattern = re.compile(rf"^###\s+\d+[.、\s]*.*{re.escape(section_keyword)}.*$", re.M)
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^###\s+\d+[.、\s]+", markdown[start:], re.M)
    end = start + next_match.start() if next_match else len(markdown)
    return markdown[start:end]


def extract_summary(markdown: str) -> dict[str, object]:
    summary = find_section(markdown, "结论摘要")
    note = extract_note_block(markdown)
    result: dict[str, object] = {
        "fundamental": find_key_value(summary, "基本面判断") or "未提取",
        "quality": find_key_value(summary, "财务质量") or "未提取",
        "valuation": find_key_value(summary, "估值状态") or "未提取",
        "fraud": find_key_value(summary, "财务造假风险初筛") or "未提取",
        "reasons": extract_numbered_after(summary, "核心理由")[:5],
        "risks": extract_numbered_after(note, "主要风险")[:4],
        "note_block": note,
    }
    if not result["risks"]:
        risk_section = find_section(markdown, "负面信息与风险排查")
        result["risks"] = extract_bullets(risk_section)[:4]
    return result


def find_key_value(text: str, key: str) -> str:
    pattern = re.compile(rf"{re.escape(key)}[：:]\s*(.+)")
    for line in text.splitlines():
        match = pattern.search(strip_md(line))
        if match:
            return match.group(1).strip()
    return ""


def extract_bullets(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*[-+*]\s+(.+)$", line)
        if match:
            items.append(normalize_space(match.group(1)))
    return items


def extract_numbered_after(text: str, key: str) -> list[str]:
    if not text:
        return []
    start = text.find(key)
    if start >= 0:
        text = text[start:]
    items: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*\d+[.、]\s+(.+)$", line)
        if match:
            items.append(normalize_space(match.group(1)))
    return items


def extract_note_block(markdown: str) -> str:
    matches = re.findall(r"```(?:text|plain)?\n(.*?)```", markdown, flags=re.S)
    for block in matches:
        if "基本面速记" in block or "结论:" in block or "公司:" in block:
            return block.strip()
    return ""


def row_map(table: TableBlock) -> dict[str, list[str]]:
    return {normalize_space(row[0]): row[1:] for row in table.rows if row}


def latest_value_from_row(table: TableBlock, row_name: str) -> tuple[str, str]:
    rows = row_map(table)
    values = rows.get(row_name)
    if not values:
        return "", ""
    headers = table.headers[1:]
    missing_values = {"未披露", "不适用", "无法判断", "无", "--", "-"}
    for idx in range(min(len(values), len(headers)) - 1, -1, -1):
        header = normalize_space(headers[idx])
        value = normalize_space(values[idx])
        if value and value not in missing_values and header not in {"变化解读", "解读"}:
            return value, header
    return "", ""


def extract_metric_from_tables(tables: list[TableBlock], metric: str) -> tuple[str, str]:
    for table in tables:
        value, period = latest_value_from_row(table, metric)
        if value:
            return value, period
    return "", ""


def extract_valuation_snapshot(tables: list[TableBlock]) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for table in tables:
        headers = [normalize_space(h) for h in table.headers]
        if "项目" in headers and "最新数据" in headers:
            rows = row_map(table)
            for item in ("收盘价", "总市值", "流通市值", "PE", "PB", "PS", "股息率"):
                vals = rows.get(item)
                if vals:
                    result[item] = (normalize_space(vals[0]), normalize_space(vals[1]) if len(vals) > 1 else "")
        if "指标" in headers and any("当前" in h or "Q1" in h for h in headers):
            rows = row_map(table)
            period_idx = max(0, len(headers) - 3)
            for item in ("收盘价", "总市值", "流通市值", "PE", "PB", "PS", "股息率"):
                vals = rows.get(item)
                if vals:
                    idx = min(period_idx, len(vals) - 1)
                    result[item] = (normalize_space(vals[idx]), "")
    return result


def extract_text_valuation(markdown: str) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    patterns = {
        "收盘价": (r"收盘价\s*([0-9,.]+)\s*元", "元"),
        "总市值": (r"总市值\s*约?\s*([0-9,.]+)\s*亿", "亿元"),
        "流通市值": (r"流通市值\s*约?\s*([0-9,.]+)\s*亿", "亿元"),
        "PE": (r"(?:TTM\s*)?PE\s*约?\s*([0-9,.]+x?)", ""),
        "PB": (r"PB\s*约?\s*([0-9,.]+x?)", ""),
        "PS": (r"PS\s*约?\s*([0-9,.]+x?)", ""),
    }
    for key, (pattern, unit) in patterns.items():
        match = re.search(pattern, markdown, flags=re.I)
        if match:
            value = match.group(1)
            if unit and unit not in value:
                value = f"{value} {unit}"
            if key in {"PE", "PB", "PS"} and not value.lower().endswith("x"):
                value = f"{value}x"
            result[key] = (value, "")
    date_match = re.search(r"截至\s*([0-9]{4}-[0-9]{2}-[0-9]{2})[^。\n]*收盘", markdown)
    if date_match:
        date_text = date_match.group(1)
        for key in ("收盘价", "总市值", "流通市值", "PE", "PB", "PS"):
            if key in result:
                result[key] = (result[key][0], date_text)
    return result


def extract_data_meta(markdown: str) -> tuple[str, str]:
    boundary = find_section(markdown, "信息边界")
    data_date = find_key_value(boundary, "数据日期") or "未提取"
    sources = find_key_value(boundary, "主要数据来源") or "详见信息边界章节"
    return data_date, sources


def build_stat_cards(valuation: dict[str, tuple[str, str]]) -> str:
    preferred = [("收盘价", "收盘价"), ("总市值", "总市值"), ("PE", "PE"), ("PB", "PB")]
    cards: list[str] = []
    for key, label in preferred:
        value, sub = valuation.get(key, ("未披露", ""))
        cards.append(
            '<div><div class="ms-v">'
            f"{inline_md(value)}"
            f'</div><div class="ms-l">{html.escape(label)}'
            f"{' · ' + html.escape(sub) if sub else ''}</div></div>"
        )
    return "\n".join(cards)


def build_badges(summary: dict[str, object]) -> str:
    return "\n".join(
        [
            f'<span class="badge fund"><span class="k">基本面</span> {inline_md(str(summary["fundamental"]))}</span>',
            f'<span class="badge qual"><span class="k">财务质量</span> {inline_md(str(summary["quality"]))}</span>',
            f'<span class="badge valu"><span class="k">估值</span> {inline_md(str(summary["valuation"]))}</span>',
            f'<span class="badge fraud"><span class="k">造假风险初筛</span> {inline_md(str(summary["fraud"]))}</span>',
        ]
    )


def list_html(items: list[str], fallback: str) -> str:
    if not items:
        items = [fallback]
    return "<ul>\n" + "\n".join(f"<li>{inline_md(item)}</li>" for item in items) + "\n</ul>"


def build_kpis(tables: list[TableBlock], valuation: dict[str, tuple[str, str]]) -> str:
    metrics = [
        ("归母净利润", "归母净利"),
        ("扣非归母净利润", "扣非净利"),
        ("毛利率", "毛利率"),
        ("经营现金流净额", "经营现金流"),
        ("应收账款/合同资产", "应收/合同资产"),
        ("存货", "存货"),
    ]
    cards: list[str] = []
    for key, label in metrics:
        value, period = extract_metric_from_tables(tables, key)
        if value:
            cls = value_class(value)
            class_attr = f" {cls}" if cls else ""
            cards.append(
                '<div class="kpi">'
                f'<div class="kl">{inline_md(period + " " if period else "")}{html.escape(label)}</div>'
                f'<div class="kv{class_attr}">{inline_md(value)}</div>'
                f'<div class="ks">{html.escape(key)}</div></div>'
            )
        if len(cards) >= 6:
            break
    if len(cards) < 4:
        for label in ("总市值", "PE", "PB", "PS"):
            value, date = valuation.get(label, ("", ""))
            if value:
                cards.append(
                    '<div class="kpi">'
                    f'<div class="kl">{html.escape(label)}</div>'
                    f'<div class="kv">{inline_md(value)}</div>'
                    f'<div class="ks">{inline_md(date) if date else "当前估值"}</div></div>'
                )
            if len(cards) >= 6:
                break
    return "\n".join(cards)


def build_toc(toc: list[tuple[str, str, str]]) -> str:
    return "\n".join(
        f'<a href="#{html.escape(sid)}"><span class="toc-num">{html.escape(num)}</span>{inline_md(title)}</a>'
        for sid, num, title in toc
    )


def safe_filename_part(text: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    cleaned = re.sub(r"\s+", "", cleaned)
    return cleaned or "未命名"


def date_stamp(value: str | None) -> str:
    if value:
        return value
    return dt.datetime.now().strftime("%Y%m%d")


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    suffix = dt.datetime.now().strftime("_%H%M%S")
    return path.with_name(f"{path.stem}{suffix}{path.suffix}")


def derive_output_path(reports_root: Path, ticker: str, company: str, date_text: str, suffix: str) -> Path:
    code_match = re.search(r"\d{6}", ticker)
    code = code_match.group(0) if code_match else safe_filename_part(ticker)
    filename = f"{safe_filename_part(company)}_{code}_基本面分析_{date_text}{suffix}"
    return reports_root / code / "基本面分析" / filename


def render_report(markdown: str, template: str, args: argparse.Namespace) -> tuple[str, dict[str, str]]:
    title = extract_title(markdown)
    company, ticker = extract_company_and_ticker(title, markdown, args.company, args.ticker)
    exchange = args.exchange or exchange_from_ticker(ticker)
    tables = collect_tables(markdown)
    valuation = extract_valuation_snapshot(tables)
    text_valuation = extract_text_valuation(markdown)
    for key, value in text_valuation.items():
        if key not in valuation or valuation[key][0] in {"", "未披露", "不适用"}:
            valuation[key] = value
    summary = extract_summary(markdown)
    rendered = render_markdown(markdown)
    data_date, sources = extract_data_meta(markdown)

    subtitle = args.subtitle or "基本面、财务质量、估值与风险初筛"
    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    replacements = {
        "title": f"{company}({ticker})基本面分析",
        "company": company,
        "ticker": ticker,
        "exchange": exchange,
        "subtitle": subtitle,
        "data_meta": data_date,
        "generated_at": generated_at,
        "stat_cards": build_stat_cards(valuation),
        "verdict_badges": build_badges(summary),
        "verdict_points": list_html(summary["reasons"], "结论理由详见正文。"),
        "risk_points": list_html(summary["risks"], "主要风险详见负面信息与风险排查、财务质量验证章节。"),
        "kpi_cards": build_kpis(tables, valuation),
        "toc": build_toc(rendered.toc),
        "content_html": rendered.html,
        "note_block": html.escape(str(summary.get("note_block") or "未提取到基本面速记块。")),
        "sources": inline_md(sources),
        "footer_meta": f"报告主体:{company}({ticker}) | 数据口径:{data_date}",
    }
    html_out = template
    for key, value in replacements.items():
        html_out = html_out.replace("{{" + key + "}}", value)
    return html_out, {"company": company, "ticker": ticker}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a fundamental-stock-review Markdown report to standalone HTML.")
    parser.add_argument("markdown", type=Path, help="Input Markdown report.")
    parser.add_argument("--output-html", type=Path, help="Output HTML path. If omitted, derive from --reports-root.")
    parser.add_argument("--copy-md", action="store_true", help="Copy the Markdown into the derived report folder with the same date naming rule.")
    parser.add_argument("--output-md", type=Path, help="Output Markdown copy path.")
    parser.add_argument("--reports-root", type=Path, default=Path.cwd() / "reports", help="Reports root used when deriving output paths.")
    parser.add_argument("--date", help="Date stamp for generated filenames, e.g. 20260704.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="HTML template path.")
    parser.add_argument("--company", help="Company short name override.")
    parser.add_argument("--ticker", help="Ticker override, e.g. 002709.SZ.")
    parser.add_argument("--exchange", help="Exchange display override.")
    parser.add_argument("--subtitle", help="Subtitle override.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    markdown_path = args.markdown.resolve()
    if not markdown_path.exists():
        print(f"Markdown not found: {markdown_path}", file=sys.stderr)
        return 2
    if not args.template.exists():
        print(f"Template not found: {args.template}", file=sys.stderr)
        return 2

    markdown = markdown_path.read_text(encoding="utf-8")
    template = args.template.read_text(encoding="utf-8")
    html_out, meta = render_report(markdown, template, args)
    date_text = date_stamp(args.date)

    output_html = args.output_html
    if output_html is None:
        output_html = derive_output_path(args.reports_root, meta["ticker"], meta["company"], date_text, ".html")
        output_html = unique_path(output_html)
    output_html = output_html.resolve()
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html_out, encoding="utf-8")

    output_md = args.output_md
    if output_md is None and args.copy_md:
        output_md = derive_output_path(args.reports_root, meta["ticker"], meta["company"], date_text, ".md")
        output_md = unique_path(output_md)
    if output_md is not None:
        output_md = output_md.resolve()
        output_md.parent.mkdir(parents=True, exist_ok=True)
        if output_md != markdown_path:
            shutil.copyfile(markdown_path, output_md)

    print(f"HTML: {output_html}")
    if output_md is not None:
        print(f"MD: {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
