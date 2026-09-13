#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import shutil
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "assets" / "fundamental_report_template.html"
FORECAST_HEADING_TERMS = ("财务预报", "业绩预报", "盈利预告", "业绩预告", "盈喜", "盈警")


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
    placeholders: list[tuple[str, str]] = []

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2).strip()
        parsed = urllib.parse.urlparse(url)
        is_web = parsed.scheme in {"http", "https"}
        is_relative = not parsed.scheme and not url.startswith(("//", "/", "\\"))
        if not (is_web or is_relative):
            return match.group(0)
        href = urllib.parse.quote(url, safe="/:?&=%#@+;,._~-()")
        target = ' target="_blank" rel="noopener"' if is_web else ""
        token = f"@@CODEXLINK{len(placeholders)}@@"
        placeholders.append(
            (token, f'<a href="{html.escape(href, quote=True)}"{target}>{html.escape(label)}</a>')
        )
        return token

    protected = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, text.strip())
    escaped = html.escape(protected)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    for token, link_html in placeholders:
        escaped = escaped.replace(token, link_html)
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


def table_to_html(
    headers: list[str],
    rows: list[list[str]],
    *,
    collapsible: bool = False,
    summary: str = "查看原始财务明细（含口径与同比）",
) -> str:
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
    table_html = "\n".join(out)
    if not collapsible:
        return table_html
    return (
        '<details class="detail-table">'
        f'<summary>{html.escape(summary)}</summary>'
        f'{table_html}'
        '</details>'
    )


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
    active_section_title = ""
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
            collapse_table = active_section_title in {"核心财务指标", "近两年财报趋势与业务结构"}
            out.append(table_to_html(headers, rows, collapsible=collapse_table))
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
                active_section_title = title
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


def is_forecast_table(table: TableBlock) -> bool:
    heading = normalize_space(table.heading)
    return any(term in heading for term in FORECAST_HEADING_TERMS) or "隐含最新单季度" in heading


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


def find_subsection(markdown: str, subsection_keyword: str) -> str:
    pattern = re.compile(rf"^(#{{4,6}})\s+.*{re.escape(subsection_keyword)}.*$", re.M)
    match = pattern.search(markdown)
    if not match:
        return ""
    level = len(match.group(1))
    start = match.end()
    next_heading = re.search(rf"^#{{2,{level}}}\s+", markdown[start:], re.M)
    end = start + next_heading.start() if next_heading else len(markdown)
    return markdown[start:end]


def strip_summary_headline_from_body(markdown: str) -> str:
    """Keep the headline in Markdown source but render it only in the top verdict."""
    lines = markdown.splitlines()
    output: list[str] = []
    in_summary = False
    for line in lines:
        if re.match(r"^###\s+\d+[.、\s]*.*结论摘要.*$", line):
            in_summary = True
            output.append(line)
            continue
        if in_summary and re.match(r"^###\s+\d+[.、\s]+", line):
            in_summary = False
        if in_summary and re.search(r"一句话结论[：:]", strip_md(line)):
            continue
        output.append(line)
    return "\n".join(output)


def extract_summary(markdown: str) -> dict[str, object]:
    summary = find_section(markdown, "结论摘要")
    note = extract_note_block(markdown)
    result: dict[str, object] = {
        "headline": find_key_value(summary, "一句话结论") or "综合结论详见核心理由与主要风险。",
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
        if value and value not in missing_values and "解读" not in header:
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


def table_cell(table: TableBlock | None, row_name: str, header_terms: tuple[str, ...]) -> str:
    if table is None:
        return ""
    headers = [normalize_space(header) for header in table.headers[1:]]
    rows = row_map(table)
    values = rows.get(row_name)
    if not values:
        return ""
    for idx, header in enumerate(headers):
        if any(term in header for term in header_terms) and idx < len(values):
            return normalize_space(values[idx])
    return ""


def first_forecast_table(tables: list[TableBlock], term: str) -> TableBlock | None:
    for table in tables:
        if term in normalize_space(table.heading):
            return table
    return None


def build_forecast_panel(markdown: str, tables: list[TableBlock]) -> str:
    subsection = find_subsection(markdown, "财务预报")
    if not subsection:
        return ""
    if "近30日未披露新的正式财务预报" in normalize_space(subsection):
        return (
            '<section class="forecast-panel forecast-empty" aria-label="最新财务预报">'
            '<div class="forecast-head"><div><span class="forecast-kicker">最新财务预报</span>'
            '<h2>近30日未披露新的正式财务预报</h2></div>'
            '<span class="forecast-tag neutral">无新增预报</span></div></section>'
        )

    cumulative = first_forecast_table(tables, "累计业绩预报")
    implied = first_forecast_table(tables, "隐含最新单季度")
    if cumulative is None:
        return ""

    period = table_cell(cumulative, "预报期间", ("本期预报区间", "预报数据", "本期")) or "最新报告期"
    info_quality = find_key_value(subsection, "信息可信度") or "待判断"
    earnings_quality = find_key_value(subsection, "盈利质量判断") or "待判断"
    info_quality = re.split(r"[（(，,；;。]", info_quality, maxsplit=1)[0].strip()
    earnings_quality = re.split(r"[（(，,；;。]", earnings_quality, maxsplit=1)[0].strip()

    cards: list[tuple[str, str, str]] = []
    cumulative_rows = (
        ("预报归母净利润", "累计归母净利润"),
        ("预报扣非归母净利润", "累计扣非净利润"),
        ("预报营业收入", "累计营业收入"),
    )
    for row_name, label in cumulative_rows:
        value = table_cell(cumulative, row_name, ("本期预报区间", "预报数据", "本期"))
        yoy = table_cell(cumulative, row_name, ("同比变化", "同比"))
        if value and value not in {"未披露", "不适用", "-", "--"}:
            cards.append((label, value, f"累计同比 {yoy}" if yoy else "累计同比未披露"))
        if len(cards) >= 2:
            break

    implied_value = table_cell(implied, "隐含单季归母净利润", ("隐含本季度区间", "本季度"))
    implied_yoy = table_cell(implied, "隐含单季归母净利润", ("单季同比",))
    implied_qoq = table_cell(implied, "隐含单季归母净利润", ("单季环比",))
    if implied_value and implied_value not in {"未披露", "不适用", "-", "--"}:
        comparison = " · ".join(part for part in (
            f"同比 {implied_yoy}" if implied_yoy else "",
            f"环比 {implied_qoq}" if implied_qoq else "",
        ) if part)
        cards.append(("隐含最新单季归母净利润", implied_value, comparison or "单季同比/环比未披露"))

    if not cards:
        return ""

    cards_html = "\n".join(
        '<div class="forecast-card">'
        f'<div class="forecast-label">{html.escape(label)}</div>'
        f'<div class="forecast-value">{html.escape(value)}</div>'
        f'<div class="forecast-change">{html.escape(change)}</div></div>'
        for label, value, change in cards[:3]
    )
    return (
        '<section class="forecast-panel" aria-label="最新财务预报">'
        '<div class="forecast-head"><div><span class="forecast-kicker">最新财务预报</span>'
        f'<h2>{html.escape(period)}</h2></div><div class="forecast-tags">'
        '<span class="forecast-tag warn">未经审计</span>'
        f'<span class="forecast-tag">信息可信度 {html.escape(info_quality)}</span>'
        f'<span class="forecast-tag">盈利质量 {html.escape(earnings_quality)}</span>'
        '</div></div>'
        f'<div class="forecast-grid">{cards_html}</div>'
        '<p class="forecast-note">隐含单季数据根据累计预报和已披露财报推算，并非公司直接披露；正式结果以定期报告为准。</p>'
        '</section>'
    )


def build_update_panel(markdown: str) -> str:
    update = find_subsection(markdown, "与上次报告相比")
    if not update.strip():
        return ""
    rendered = render_markdown(update).html
    return (
        '<section class="update-panel" aria-label="本次更新">'
        '<div class="update-head"><span>RESEARCH CONTINUITY</span><h2>本次更新 · 与上次报告相比</h2></div>'
        f'<div class="update-body">{rendered}</div>'
        '</section>'
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
    actual_tables = [table for table in tables if not is_forecast_table(table)]
    cards: list[str] = []
    for key, label in metrics:
        value, period = extract_metric_from_tables(actual_tables, key)
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


MISSING_CHART_VALUES = {"", "未披露", "不适用", "无法判断", "无", "--", "-"}
CHART_COLORS = ("#1f5d8f", "#b65c3b", "#427a62", "#8060a8")


def numeric_value(value: str) -> float | None:
    clean = normalize_space(value).replace(",", "")
    if clean in MISSING_CHART_VALUES:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", clean)
    return float(match.group(0)) if match else None


def comparable_columns(table: TableBlock) -> list[tuple[int, str]]:
    ignored = ("解读", "变化", "同比", "环比", "质量", "备注", "来源")
    return [(i, normalize_space(header)) for i, header in enumerate(table.headers[1:]) if normalize_space(header) and not any(term in normalize_space(header) for term in ignored)]


def first_table_matching(tables: list[TableBlock], term: str) -> TableBlock | None:
    return next((table for table in tables if term in normalize_space(table.heading)), None)


def table_metric_series(table: TableBlock | None, metrics: list[tuple[str, str]]) -> list[tuple[str, list[tuple[str, float]]]]:
    if table is None:
        return []
    rows = row_map(table)
    columns = comparable_columns(table)
    result: list[tuple[str, list[tuple[str, float]]]] = []
    for row_name, label in metrics:
        values = rows.get(row_name)
        if not values:
            continue
        points = [(period, number) for index, period in columns if index < len(values) and (number := numeric_value(values[index])) is not None]
        if len(points) >= 2:
            result.append((label, points))
    return result


def chart_value_label(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def chart_periods(series: list[tuple[str, list[tuple[str, float]]]]) -> list[str]:
    return list(dict.fromkeys(period for _, points in series for period, _ in points))


def grouped_bar_svg(series: list[tuple[str, list[tuple[str, float]]]]) -> str:
    periods = chart_periods(series)
    if not series or len(periods) < 2:
        return ""
    width, height, left, right, top, bottom = 720, 290, 44, 18, 50, 48
    values = [value for _, points in series for _, value in points]
    low, high = min(0.0, min(values)), max(0.0, max(values))
    if low == high:
        high += 1.0
    plot_width, plot_height = width - left - right, height - top - bottom
    baseline = top + (high / (high - low)) * plot_height
    group_width = plot_width / len(periods)
    bar_width = min(28.0, max(7.0, (group_width - 14.0) / len(series)))
    bits = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="经营规模与利润趋势柱状图">', f'<line x1="{left}" x2="{width-right}" y1="{baseline:.1f}" y2="{baseline:.1f}" class="chart-axis"/>', f'<text x="{left}" y="22" class="chart-unit">单位：亿元</text>']
    for index, (label, _) in enumerate(series):
        x = left + index * 138
        color = CHART_COLORS[index % len(CHART_COLORS)]
        bits.extend((f'<rect x="{x}" y="29" width="10" height="10" rx="2" fill="{color}"/>', f'<text x="{x+15}" y="38" class="chart-legend">{html.escape(label)}</text>'))
    for period_index, period in enumerate(periods):
        centre = left + period_index * group_width + group_width / 2
        start = centre - ((len(series) - 1) * bar_width) / 2
        bits.append(f'<text x="{centre:.1f}" y="{height-16}" text-anchor="middle" class="chart-label">{html.escape(period)}</text>')
        for series_index, (_, points) in enumerate(series):
            value = dict(points).get(period)
            if value is None:
                continue
            y = top + (high - value) / (high - low) * plot_height
            bar_y, bar_height = min(y, baseline), max(1.0, abs(baseline - y))
            x = start + series_index * bar_width
            color = CHART_COLORS[series_index % len(CHART_COLORS)]
            bits.extend((f'<rect x="{x:.1f}" y="{bar_y:.1f}" width="{bar_width-2:.1f}" height="{bar_height:.1f}" rx="2" fill="{color}"/>', f'<text x="{x+(bar_width-2)/2:.1f}" y="{bar_y-5 if value >= 0 else bar_y+bar_height+12:.1f}" text-anchor="middle" class="chart-value">{chart_value_label(value)}</text>'))
    return "".join(bits) + "</svg>"


def quality_svg(series: list[tuple[str, list[tuple[str, float]]]]) -> str:
    if not series:
        return ""
    width, row_height, top, bottom, left, right = 720, 64, 16, 30, 126, 18
    height, plot_width = top + bottom + row_height * len(series), width - left - right
    bits = [f'<svg class="chart-svg quality-svg" viewBox="0 0 {width} {height}" role="img" aria-label="盈利与现金质量趋势图">']
    for series_index, (label, points) in enumerate(series):
        values = [value for _, value in points]
        low, high = min(values), max(values)
        if low == high:
            low, high = low - 1, high + 1
        y_top, y_bottom = top + series_index * row_height + 9, top + (series_index + 1) * row_height - 18
        coords = []
        for index, (period, value) in enumerate(points):
            x = left + index * plot_width / max(1, len(points) - 1)
            y = y_bottom - (value - low) / (high - low) * (y_bottom - y_top)
            coords.append((x, y, period, value))
        color = CHART_COLORS[series_index % len(CHART_COLORS)]
        bits.extend((f'<text x="8" y="{y_top+11:.1f}" class="chart-series-label">{html.escape(label)}</text>', f'<line x1="{left}" x2="{width-right}" y1="{y_bottom:.1f}" y2="{y_bottom:.1f}" class="chart-grid"/>', f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(f"{x:.1f},{y:.1f}" for x,y,_,_ in coords)}"/>'))
        for x, y, period, value in coords:
            bits.extend((f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>', f'<text x="{x:.1f}" y="{y-8:.1f}" text-anchor="middle" class="chart-value">{chart_value_label(value)}</text>'))
            if series_index == len(series) - 1:
                bits.append(f'<text x="{x:.1f}" y="{height-8}" text-anchor="middle" class="chart-label">{html.escape(period)}</text>')
    return "".join(bits) + "</svg>"


def business_bar_svg(table: TableBlock | None) -> str:
    if table is None:
        return ""
    headers = [normalize_space(header) for header in table.headers[1:]]
    latest_index = next((i for i, header in enumerate(headers) if "最新" in header and "收入" in header), None)
    if latest_index is None:
        return ""
    entries = [(normalize_space(row[0]), value) for row in table.rows if len(row) > latest_index + 1 and (value := numeric_value(row[latest_index + 1])) is not None]
    if len(entries) < 2:
        return ""
    width, row_height, top, bottom, left, right = 720, 40, 18, 26, 174, 70
    height, plot_width, max_value = top + bottom + row_height * len(entries), width - left - right, max(value for _, value in entries)
    bits = [f'<svg class="chart-svg business-svg" viewBox="0 0 {width} {height}" role="img" aria-label="业务收入结构条形图">']
    for index, (name, value) in enumerate(entries):
        y, bar_width, color = top + index * row_height, value / max_value * plot_width, CHART_COLORS[index % len(CHART_COLORS)]
        bits.extend((f'<text x="{left-10}" y="{y+23}" text-anchor="end" class="chart-label">{html.escape(name)}</text>', f'<rect x="{left}" y="{y+7}" width="{plot_width}" height="21" rx="3" class="chart-track"/>', f'<rect x="{left}" y="{y+7}" width="{bar_width:.1f}" height="21" rx="3" fill="{color}"/>', f'<text x="{left+bar_width+7:.1f}" y="{y+23}" class="chart-value">{chart_value_label(value)} 亿元</text>'))
    return "".join(bits) + "</svg>"


def chart_card(title: str, note: str, svg: str, unavailable: str) -> str:
    body = f'<div class="chart-body">{svg}</div>' if svg else f'<div class="chart-empty">{html.escape(unavailable)}</div>'
    return f'<article class="chart-card"><h3>{html.escape(title)}</h3>{body}<p class="chart-meta">{note}</p></article>'


def build_financial_visuals(markdown: str, tables: list[TableBlock], data_date: str, sources: str) -> str:
    financial = first_table_matching(tables, "最近三年年度财报") or first_table_matching(tables, "近两年财报趋势")
    periods = " / ".join(period for _, period in comparable_columns(financial)) if financial else data_date
    source_html = inline_md(sources)
    financial_note = f'<b>数据期间：</b>{html.escape(periods)} <b>口径：</b>以核心财务指标表的合并报表数据为准。<br><b>来源：</b>{source_html}'
    scale = grouped_bar_svg(table_metric_series(financial, [("营业收入", "营业收入"), ("归母净利润", "归母净利润"), ("扣非归母净利润", "扣非净利润")]))
    quality = quality_svg(table_metric_series(financial, [("毛利率", "毛利率"), ("扣非净利率", "扣非净利率"), ("ROE", "ROE"), ("经营现金流/净利润", "经营现金流/净利润")]))
    return '<section class="financial-visuals" aria-label="财务图表速览"><div class="visuals-head"><div><span>FINANCIAL VISUALS</span><h2>财务趋势</h2></div><p>图表优先展示趋势；原始表格保留在对应章节，可展开核对。</p></div><div class="chart-grid">' + chart_card("经营规模与利润趋势", financial_note, scale, "核心财务表未提供连续两期的收入和利润数据。") + chart_card("盈利与现金质量趋势", financial_note, quality, "核心财务表未提供连续两期的利润率、ROE 或现金质量数据。") + '</div></section>'


def build_decision_card(markdown: str) -> str:
    decision = find_subsection(markdown, "当前位置与交易决策")
    source_record = extract_note_block(markdown)
    if not decision and not source_record:
        return ""

    def field_value(*keys: str) -> str:
        for key in keys:
            value = find_key_value(decision, key) or find_key_value(source_record, key)
            if value:
                return value
        return ""

    action = field_value("当前动作") or "详见正文"
    position = field_value("仓位速览", "建议目标仓位") or "详见正文"
    execution = field_value("观察条件速览", "参考价格与计划买入区间", "入场条件") or "详见正文"
    stop = field_value("止损速览", "价格止损") or "详见正文"
    risk = field_value("基本面提前退出条件") or "详见正文"
    hide_details = normalize_space(field_value("持仓状态")) == "未持仓" and normalize_space(action) == "等待"

    def condition_list(value: str) -> str:
        return '<ul>' + ''.join('<li>' + inline_md(item.strip()) + '</li>' for item in value.split('；') if item.strip()) + '</ul>'

    details = ''.join('<div><dt>' + label + '</dt><dd>' + inline_md(field_value(key) or "详见正文") + '</dd></div>' for label, key in [
        ("建议仓位", "建议目标仓位"),
        ("执行 / 观察条件", "参考价格与计划买入区间"),
        ("价格止损", "价格止损"),
        ("基本面提前退出条件", "基本面提前退出条件"),
    ])
    details_panel = '' if hide_details else '<details class="decision-details"><summary>查看仓位与止损完整说明</summary><dl>' + details + '</dl></details>'
    return (
        '<section class="decision-card" aria-label="交易决策摘要"><h3>当前位置与交易决策</h3>'
        '<div class="decision-summary"><strong class="decision-action">' + inline_md(action) + '</strong><span>' + inline_md(position) + '</span></div>'
        '<div class="decision-columns"><div class="decision-condition"><h4>执行 / 观察条件</h4>' + condition_list(execution) + '</div>'
        '<div class="decision-condition"><h4>失效 / 重审条件</h4><p><strong>价格止损：</strong>' + inline_md(stop) + '</p>' + condition_list(risk) + '</div></div>'
        + details_panel + '</section>'
    )


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
    rendered = render_markdown(strip_summary_headline_from_body(markdown))
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
        "verdict_headline": inline_md(str(summary["headline"])),
        "decision_card": build_decision_card(markdown),
        "verdict_points": list_html(summary["reasons"], "结论理由详见正文。"),
        "risk_points": list_html(summary["risks"], "主要风险详见负面信息与风险排查、财务质量验证章节。"),
        "kpi_cards": build_kpis(tables, valuation),
        "financial_visuals": build_financial_visuals(markdown, tables, data_date, sources),
        "forecast_panel": build_forecast_panel(markdown, tables),
        "update_panel": build_update_panel(markdown),
        "toc": build_toc(rendered.toc),
        "content_html": rendered.html,
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
