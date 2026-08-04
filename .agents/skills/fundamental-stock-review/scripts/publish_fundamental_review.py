#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import tempfile
import urllib.parse
from pathlib import Path
from types import SimpleNamespace

from render_fundamental_html import DEFAULT_TEMPLATE, render_report


SNAPSHOT_RE = re.compile(r"_基本面分析_(20\d{6})(?:_(\d{6}))?(?:_(\d{6}))?\.md$")
TITLE_RE = re.compile(
    r"^#\s+(.+?)[（(](\d{6}(?:\.(?:SZ|SH|BJ))?)(?:\s*/\s*[^）)]+)?[）)]",
    re.M | re.I,
)
CONCLUSION_KEYS = ("基本面判断", "财务质量", "估值状态", "财务造假风险初筛")


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def strip_md(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[*_`>#]+", "", value)
    return re.sub(r"\s+", " ", value).strip(" -+\t")


def safe_part(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|\s]+", "_", value.strip()).strip("_")
    return value or "未命名"


def extract_identity(markdown: str) -> tuple[str, str, str]:
    match = TITLE_RE.search(markdown)
    if not match:
        raise ValueError("H1 标题中未识别到公司简称和六位股票代码")
    company = strip_md(match.group(1))
    ticker = match.group(2).upper()
    code_match = re.search(r"\d{6}", ticker)
    if not code_match:
        raise ValueError("未识别到六位股票代码")
    code = code_match.group(0)
    if "." not in ticker:
        ticker += ".SH" if code.startswith("6") else ".BJ" if code.startswith(("4", "8")) else ".SZ"
    return company, ticker, code


def extract_key(markdown: str, key: str) -> str:
    section = find_section(markdown, "结论摘要") or markdown
    for line in section.splitlines():
        clean = strip_md(line)
        match = re.search(rf"{re.escape(key)}[：:]\s*(.+)", clean)
        if match:
            return match.group(1).strip().rstrip("。")
    return "未结构化"


def extract_headline(markdown: str) -> str:
    section = find_section(markdown, "结论摘要") or markdown
    for text in (section, markdown):
        for line in text.splitlines():
            clean = strip_md(line)
            match = re.search(r"一句话结论[：:]\s*(.+)", clean)
            if match:
                return match.group(1).strip()
    return "历史报告未使用可提取的一句话结论格式。"


def find_section(markdown: str, keyword: str) -> str:
    match = re.search(rf"^###\s+\d+[.、\s]*.*{re.escape(keyword)}.*$", markdown, re.M)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^###\s+\d+[.、\s]+", markdown[start:], re.M)
    return markdown[start : start + next_match.start()] if next_match else markdown[start:]


def extract_field(markdown: str, key: str, fallback: str = "未披露") -> str:
    for line in markdown.splitlines():
        clean = strip_md(line)
        match = re.search(rf"{re.escape(key)}[：:]\s*(.+)", clean)
        if match:
            return match.group(1).strip()
    return fallback


def snapshot_sort_key(path: Path) -> tuple[str, str, str, str]:
    match = SNAPSHOT_RE.search(path.name)
    if not match:
        return ("00000000", "000000", "000000", path.name)
    return (match.group(1), match.group(2) or "000000", match.group(3) or "000000", path.name)


def snapshot_display(path: Path) -> str:
    date_text, time_text, _, _ = snapshot_sort_key(path)
    if date_text == "00000000":
        return path.name
    value = f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:8]}"
    if time_text != "000000":
        value += f" {time_text[:2]}:{time_text[2:4]}:{time_text[4:6]}"
    return value


def collect_snapshots(report_dir: Path) -> list[Path]:
    return sorted(
        (path for path in report_dir.glob("*.md") if SNAPSHOT_RE.search(path.name)),
        key=snapshot_sort_key,
    )


def detect_trigger(markdown: str, first: bool) -> str:
    if first:
        return "首次建立研究基线"
    forecast = find_section(markdown, "核心财务指标")
    normalized_forecast = re.sub(r"\s+", "", forecast)
    if any(term in forecast for term in ("业绩预告", "财务预报", "盈喜", "盈警")) and "近30日未披露新的正式财务预报" not in normalized_forecast:
        return "财务预报/业绩预告更新"
    if any(term in markdown for term in ("会计差错更正", "前期差错更正")):
        return "会计更正复盘"
    return "定期基本面复盘"


def conclusion_change(previous: dict[str, str] | None, current: dict[str, str]) -> str:
    if previous is None:
        return "建立基线"
    changes = [f"{key}：{previous.get(key, '未结构化')}→{current[key]}" for key in CONCLUSION_KEYS if previous.get(key) != current[key]]
    return "；".join(changes) if changes else "四项核心结论未变"


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    try:
        shutil.copyfile(source, temp_name)
        os.replace(temp_name, destination)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def render_snapshot(markdown_path: Path, html_path: Path) -> None:
    markdown = markdown_path.read_text(encoding="utf-8")
    template = DEFAULT_TEMPLATE.read_text(encoding="utf-8")
    args = SimpleNamespace(company=None, ticker=None, exchange=None, subtitle=None)
    html_out, _ = render_report(markdown, template, args)
    atomic_write_text(html_path, html_out)


def markdown_link(path: Path) -> str:
    return urllib.parse.quote(path.name, safe="._-()")


def timeline_records(snapshots: list[Path]) -> tuple[list[dict[str, object]], str, str]:
    records: list[dict[str, object]] = []
    previous_conclusions: dict[str, str] | None = None
    company = ticker = ""
    for index, snapshot in enumerate(snapshots):
        markdown = snapshot.read_text(encoding="utf-8", errors="replace")
        try:
            company, ticker, _ = extract_identity(markdown)
        except ValueError:
            company = company or snapshot.name.split("_")[0]
            ticker = ticker or "未识别"
        conclusions = {key: extract_key(markdown, key) for key in CONCLUSION_KEYS}
        html_path = snapshot.with_suffix(".html")
        records.append(
            {
                "version": snapshot_display(snapshot),
                "markdown_file": snapshot.name,
                "html_file": html_path.name if html_path.exists() else "",
                "trigger": detect_trigger(markdown, index == 0),
                "coverage": extract_field(markdown, "分析范围", extract_field(markdown, "数据日期")),
                "headline": extract_headline(markdown),
                "conclusions": conclusions,
                "change": conclusion_change(previous_conclusions, conclusions),
            }
        )
        previous_conclusions = conclusions
    return records, company, ticker


def build_timeline_markdown(company: str, ticker: str, records: list[dict[str, object]]) -> str:
    lines = [
        f"# {company}（{ticker}）研究轨迹",
        "",
        f"> 本文件由不可变历史 Markdown 快照重建，更新时间：{now_iso()}。`_最新` 文件是派生副本，不作为历史真相来源。",
        "",
        "| 版本 | 触发事件 | 覆盖范围 | 基本面 | 财务质量 | 估值 | 风险初筛 | 相比上次 | 报告 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for record in records:
        conclusions = record["conclusions"]
        md = f"[MD]({markdown_link(Path(str(record['markdown_file'])))})"
        html_file = str(record["html_file"])
        html_link = f" / [HTML]({markdown_link(Path(html_file))})" if html_file else ""
        cells = (
            record["version"],
            record["trigger"],
            record["coverage"],
            conclusions["基本面判断"],
            conclusions["财务质量"],
            conclusions["估值状态"],
            conclusions["财务造假风险初筛"],
            record["change"],
            md + html_link,
        )
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")

    lines.extend(("", "## 版本结论摘要", ""))
    for record in reversed(records):
        lines.extend((f"### {record['version']} · {record['trigger']}", "", str(record["headline"]), ""))
    return "\n".join(lines) + "\n"


def build_timeline_html(company: str, ticker: str, records: list[dict[str, object]]) -> str:
    rows: list[str] = []
    cards: list[str] = []
    for record in records:
        conclusions = record["conclusions"]
        md_href = markdown_link(Path(str(record["markdown_file"])))
        html_file = str(record["html_file"])
        report_links = f'<a href="{md_href}">MD</a>'
        if html_file:
            report_links += f' / <a href="{markdown_link(Path(html_file))}">HTML</a>'
        values = (
            record["version"], record["trigger"], record["coverage"], conclusions["基本面判断"],
            conclusions["财务质量"], conclusions["估值状态"], conclusions["财务造假风险初筛"], record["change"],
        )
        rows.append("<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in values) + f"<td>{report_links}</td></tr>")
    for record in reversed(records):
        cards.append(
            f'<article><h2>{html.escape(str(record["version"]))} · {html.escape(str(record["trigger"]))}</h2>'
            f'<p>{html.escape(str(record["headline"]))}</p></article>'
        )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(company)}研究轨迹</title><style>
body{{margin:0;background:#f5f7fa;color:#1a2433;font:14px/1.65 system-ui,-apple-system,"PingFang SC",sans-serif}}
main{{max-width:1500px;margin:auto;padding:28px}}h1{{color:#1f3a5f;margin:0 0 6px}}.meta{{color:#64748b;margin-bottom:20px}}
.scroll{{overflow:auto;background:#fff;border:1px solid #d8dee7;border-radius:8px}}table{{border-collapse:collapse;width:100%;min-width:1100px}}
th,td{{padding:10px 12px;border-bottom:1px solid #edf1f5;text-align:left;vertical-align:top}}th{{background:#eaf0f8;color:#1f3a5f;white-space:nowrap}}
article{{background:#fff;border-left:4px solid #1f3a5f;margin:14px 0;padding:12px 16px;border-radius:5px}}article h2{{font-size:15px;margin:0 0 5px}}article p{{margin:0}}
a{{color:#3b5b85}}@media print{{body{{background:#fff}}main{{padding:0}}}}
</style></head><body><main><h1>{html.escape(company)}（{html.escape(ticker)}）研究轨迹</h1>
<div class="meta">由不可变历史快照重建 · 更新时间 {html.escape(now_iso())}</div>
<div class="scroll"><table><thead><tr><th>版本</th><th>触发事件</th><th>覆盖范围</th><th>基本面</th><th>财务质量</th><th>估值</th><th>风险初筛</th><th>相比上次</th><th>报告</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<section>{''.join(cards)}</section></main></body></html>"""


def write_state(report_dir: Path, company: str, ticker: str, records: list[dict[str, object]]) -> Path:
    latest = records[-1] if records else {}
    state = {
        "schema_version": 1,
        "updated_at": now_iso(),
        "company": company,
        "ticker": ticker,
        "latest_version": latest.get("version", ""),
        "latest_markdown": latest.get("markdown_file", ""),
        "latest_html": latest.get("html_file", ""),
        "current_conclusions": latest.get("conclusions", {}),
        "versions": records,
        "note": "本文件使用 JSON 语法保存；JSON 是 YAML 1.2 的有效子集，可由历史 Markdown 快照重建。",
    }
    path = report_dir / ".research" / "state.yaml"
    atomic_write_text(path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return path


def rebuild_index(report_dir: Path, refresh_latest: bool = True) -> tuple[Path, Path, Path]:
    snapshots = collect_snapshots(report_dir)
    if not snapshots:
        raise ValueError(f"未在 {report_dir} 找到日期版本 Markdown")
    records, company, ticker = timeline_records(snapshots)
    _, _, code = extract_identity(snapshots[-1].read_text(encoding="utf-8", errors="replace"))
    base = f"{safe_part(company)}_{code}"
    timeline_md = report_dir / f"{base}_研究轨迹.md"
    timeline_html = report_dir / f"{base}_研究轨迹.html"
    atomic_write_text(timeline_md, build_timeline_markdown(company, ticker, records))
    atomic_write_text(timeline_html, build_timeline_html(company, ticker, records))

    latest_snapshot = snapshots[-1]
    latest_html_snapshot = latest_snapshot.with_suffix(".html")
    if not latest_html_snapshot.exists():
        render_snapshot(latest_snapshot, latest_html_snapshot)
        records[-1]["html_file"] = latest_html_snapshot.name
    if refresh_latest:
        atomic_copy(latest_snapshot, report_dir / f"{base}_基本面分析_最新.md")
        atomic_copy(latest_html_snapshot, report_dir / f"{base}_基本面分析_最新.html")
    state_path = write_state(report_dir, company, ticker, records)
    return timeline_md, timeline_html, state_path


def validate_delta(markdown: str, has_previous: bool, allow_missing: bool) -> None:
    missing = [key for key in CONCLUSION_KEYS if extract_key(markdown, key) == "未结构化"]
    if missing:
        raise ValueError("结论摘要缺少固定字段：" + "、".join(missing))
    has_delta = bool(re.search(r"^#{4,6}\s+.*与上次报告相比", markdown, re.M))
    if has_previous and not has_delta and not allow_missing:
        raise ValueError("存在历史报告，但本次报告缺少 `与上次报告相比` 子节")
    if not has_previous and has_delta and "首次建立研究基线" not in markdown and not allow_missing:
        raise ValueError("首次报告的 `与上次报告相比` 子节应注明 `首次建立研究基线`")


def unique_snapshot_path(report_dir: Path, stem: str, suffix: str) -> Path:
    candidate = report_dir / f"{stem}{suffix}"
    if not candidate.exists():
        return candidate
    extra = dt.datetime.now().strftime("_%f")
    return report_dir / f"{stem}{extra}{suffix}"


def publish(markdown_path: Path, reports_root: Path, date_text: str | None, allow_missing_delta: bool) -> tuple[Path, Path]:
    source = markdown_path.resolve()
    markdown = source.read_text(encoding="utf-8")
    company, ticker, code = extract_identity(markdown)
    report_dir = reports_root.resolve() / code / "基本面分析"
    report_dir.mkdir(parents=True, exist_ok=True)
    has_previous = bool(collect_snapshots(report_dir))
    validate_delta(markdown, has_previous, allow_missing_delta)

    version = date_text or dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not re.fullmatch(r"20\d{6}(?:_\d{6})?", version):
        raise ValueError("--date 必须使用 YYYYMMDD 或 YYYYMMDD_HHMMSS")
    stem = f"{safe_part(company)}_{code}_基本面分析_{version}"
    snapshot_md = unique_snapshot_path(report_dir, stem, ".md")
    snapshot_html = snapshot_md.with_suffix(".html")
    atomic_write_text(snapshot_md, markdown)
    try:
        render_snapshot(snapshot_md, snapshot_html)
    except Exception:
        snapshot_md.unlink(missing_ok=True)
        snapshot_html.unlink(missing_ok=True)
        raise

    base = f"{safe_part(company)}_{code}_基本面分析_最新"
    atomic_copy(snapshot_md, report_dir / f"{base}.md")
    atomic_copy(snapshot_html, report_dir / f"{base}.html")
    rebuild_index(report_dir, refresh_latest=False)
    return snapshot_md, snapshot_html


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish continuous fundamental-review snapshots and rebuild the research timeline.")
    parser.add_argument("markdown", nargs="?", type=Path, help="Completed Markdown report to publish.")
    parser.add_argument("--reports-root", type=Path, default=Path.cwd() / "reports")
    parser.add_argument("--date", help="Snapshot date or timestamp: YYYYMMDD[_HHMMSS].")
    parser.add_argument("--rebuild-existing", type=Path, help="Rebuild latest/timeline/state for an existing 基本面分析 directory.")
    parser.add_argument("--allow-missing-delta", action="store_true", help="Allow legacy Markdown without the update-comparison subsection.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.rebuild_existing:
            timeline_md, timeline_html, state_path = rebuild_index(args.rebuild_existing.resolve())
            print(f"研究轨迹MD: {timeline_md}")
            print(f"研究轨迹HTML: {timeline_html}")
            print(f"研究状态: {state_path}")
            return 0
        if not args.markdown:
            raise ValueError("请提供待发布 Markdown，或使用 --rebuild-existing")
        snapshot_md, snapshot_html = publish(args.markdown, args.reports_root, args.date, args.allow_missing_delta)
        print(f"快照MD: {snapshot_md}")
        print(f"快照HTML: {snapshot_html}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"发布失败: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
