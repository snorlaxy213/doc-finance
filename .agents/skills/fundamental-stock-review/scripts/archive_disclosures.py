#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


PDF_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)", re.I)
DATE_SEPARATED_RE = re.compile(r"(20\d{2})[-_/](\d{1,2})[-_/](\d{1,2})(?!\d)")
DATE_COMPACT_RE = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})")
HKEX_DATE_RE = re.compile(r"sehk(\d{2})(\d{2})(\d{2})", re.I)
SAFE_RE = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff._-]+")
PDF_HOST_HINTS = ("static.cninfo.com.cn", "disc.static.szse.cn", "pdf.dfcfw.com")


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def safe_part(value: str, fallback: str) -> str:
    value = SAFE_RE.sub("_", value.strip()).strip("._-")
    return value[:80] or fallback


def is_pdf_candidate(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.path.lower().endswith(".pdf") or any(host in parsed.netloc.lower() for host in PDF_HOST_HINTS)


def classify_document(label: str) -> str:
    text = label.replace(" ", "")
    rules = (
        (("业绩预告修正", "预告修正", "盈警修正", "盈喜修正"), "业绩预告修正"),
        (("业绩预告", "盈利预告", "盈喜", "盈警"), "业绩预告"),
        (("半年度报告", "半年报", "中期报告", "中报"), "半年度报告"),
        (("年度报告", "年报"), "年度报告"),
        (("第一季度报告", "一季报"), "第一季度报告"),
        (("第三季度报告", "三季报"), "第三季度报告"),
        (("审计报告",), "审计报告"),
        (("问询函回复", "回复公告"), "问询回复"),
        (("问询函",), "问询函"),
        (("合同", "订单", "中标"), "合同订单"),
        (("处罚", "监管"), "监管公告"),
    )
    for terms, kind in rules:
        if any(term in text for term in terms):
            return kind
    return "正式披露"


def infer_period(label: str) -> str:
    text = label.replace(" ", "")
    year_match = re.search(r"(20\d{2})年?", text)
    year = year_match.group(1) if year_match else "期间待核验"
    if any(term in text for term in ("半年度", "半年报", "中期报告", "中报", "H1")):
        return f"{year}H1" if year_match else year
    if any(term in text for term in ("年度报告", "年报")):
        return f"{year}A" if year_match else year
    if any(term in text for term in ("第一季度", "一季报", "Q1")):
        return f"{year}Q1" if year_match else year
    if any(term in text for term in ("前三季度", "第三季度", "三季报", "Q3")):
        return f"{year}Q3" if year_match else year
    return year


def valid_date(year: str, month: str, day: str) -> str | None:
    try:
        value = dt.date(int(year), int(month), int(day))
    except ValueError:
        return None
    return value.strftime("%Y%m%d")


def dates_in_text(text: str) -> list[str]:
    candidates: list[tuple[int, str]] = []
    for match in DATE_SEPARATED_RE.finditer(text):
        value = valid_date(*match.groups())
        if value:
            candidates.append((match.start(), value))
    for match in DATE_COMPACT_RE.finditer(text):
        value = valid_date(*match.groups())
        if value:
            candidates.append((match.start(), value))
    for match in HKEX_DATE_RE.finditer(text):
        value = valid_date("20" + match.group(1), match.group(2), match.group(3))
        if value:
            candidates.append((match.start(), value))
    return [value for _, value in sorted(candidates)]


def infer_date(url: str, fallback: str) -> str:
    candidates = dates_in_text(url)
    return candidates[-1] if candidates else fallback


def announcement_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).stem
    if name:
        return safe_part(name, "公告标识待核验")[-48:]
    query = urllib.parse.parse_qs(parsed.query)
    for key in ("id", "announcementId", "docid"):
        if query.get(key):
            return safe_part(query[key][0], "公告标识待核验")
    return "公告标识待核验"


def load_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"schema_version": 1, "updated_at": now_iso(), "sources": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "updated_at": now_iso(), "sources": []}
    if not isinstance(data.get("sources"), list):
        data["sources"] = []
    return data


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def save_manifest(path: Path, manifest: dict[str, object]) -> None:
    manifest["updated_at"] = now_iso()
    atomic_write_text(path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def download(url: str, destination_dir: Path, timeout: int) -> tuple[Path, str, int]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 CodexDisclosureArchive/1.0",
            "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.5",
        },
    )
    fd, temp_name = tempfile.mkstemp(prefix=".download-", suffix=".pdf", dir=destination_dir)
    digest = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(fd, "wb") as output, urllib.request.urlopen(request, timeout=timeout) as response:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        temp_path = Path(temp_name)
        with temp_path.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                raise ValueError("下载内容不是有效 PDF 文件头")
        return temp_path, digest.hexdigest(), size
    except Exception:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
        raise


def pdf_pages(path: Path) -> int | None:
    executable = shutil.which("pdfinfo")
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, str(path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M)
    return int(match.group(1)) if match else None


def collect_links(report: Path) -> list[tuple[str, str]]:
    text = report.read_text(encoding="utf-8", errors="replace")
    return [(label.strip(), url.strip()) for label, url in PDF_LINK_RE.findall(text) if is_pdf_candidate(url)]


def find_by_url(entries: list[dict[str, object]], url: str) -> dict[str, object] | None:
    for entry in entries:
        if url == entry.get("official_url") or url in entry.get("alternate_urls", []):
            return entry
    return None


def find_by_hash(entries: list[dict[str, object]], digest: str) -> dict[str, object] | None:
    return next((entry for entry in entries if digest and entry.get("sha256") == digest), None)


def add_usage(entry: dict[str, object], report_name: str, url: str) -> None:
    used_by = entry.setdefault("used_by", [])
    if report_name not in used_by:
        used_by.append(report_name)
    if url != entry.get("official_url"):
        alternate = entry.setdefault("alternate_urls", [])
        if url not in alternate:
            alternate.append(url)


def archive_link(
    report_dir: Path,
    report: Path,
    label: str,
    url: str,
    entries: list[dict[str, object]],
    timeout: int,
) -> str:
    existing = find_by_url(entries, url)
    if existing and existing.get("status") == "已归档":
        add_usage(existing, report.name, url)
        return "reused"

    fallback_dates = dates_in_text(report.name)
    report_date = fallback_dates[-1] if fallback_dates else "日期待核验"
    published_date = infer_date(url, report_date)
    year = published_date[:4] if published_date[:4].isdigit() else "日期待核验"
    target_dir = report_dir / "原始资料" / year

    try:
        temp_path, digest, size = download(url, target_dir, timeout)
        duplicate = find_by_hash(entries, digest)
        if duplicate:
            temp_path.unlink(missing_ok=True)
            add_usage(duplicate, report.name, url)
            return "deduplicated"

        kind = classify_document(label)
        period = infer_period(label)
        identifier = announcement_id(url)
        filename = "_".join(
            (
                safe_part(published_date, "日期待核验"),
                safe_part(period, "期间待核验"),
                safe_part(kind, "正式披露"),
                identifier,
            )
        ) + ".pdf"
        target = target_dir / filename
        if target.exists():
            target = target.with_name(f"{target.stem}_{digest[:8]}{target.suffix}")
        os.replace(temp_path, target)
        pages = pdf_pages(target)
        entries.append(
            {
                "source_id": f"SRC-{published_date}-{digest[:8]}",
                "title": label,
                "document_type": kind,
                "period": period,
                "published_date": published_date,
                "official_url": url,
                "alternate_urls": [],
                "local_path": target.relative_to(report_dir).as_posix(),
                "sha256": digest,
                "bytes": size,
                "pages": pages,
                "retrieved_at": now_iso(),
                "used_by": [report.name],
                "status": "已归档",
            }
        )
        return "archived"
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        if existing:
            existing.update({"status": "归档失败", "error": str(exc), "last_attempt_at": now_iso()})
            add_usage(existing, report.name, url)
        else:
            entries.append(
                {
                    "source_id": f"FAILED-{hashlib.sha256(url.encode()).hexdigest()[:12]}",
                    "title": label,
                    "document_type": classify_document(label),
                    "period": infer_period(label),
                    "published_date": published_date,
                    "official_url": url,
                    "alternate_urls": [],
                    "local_path": "",
                    "sha256": "",
                    "bytes": 0,
                    "pages": None,
                    "retrieved_at": "",
                    "last_attempt_at": now_iso(),
                    "used_by": [report.name],
                    "status": "归档失败",
                    "error": str(exc),
                }
            )
        return "failed"


def md_escape(value: object) -> str:
    return str(value or "未披露").replace("|", "\\|").replace("\n", " ")


def write_index(report_dir: Path, entries: list[dict[str, object]]) -> Path:
    rows = [
        "# 原始资料索引",
        "",
        f"> 更新时间：{now_iso()}。本索引记录报告实际引用的正式披露 PDF；归档失败项保留原始链接和失败状态。",
        "",
        "| 资料编号 | 标题 | 类型/期间 | 公告日期 | 本地文件 | 官方链接 | SHA-256 | 页数 | 引用报告 | 状态 |",
        "|---|---|---|---|---|---|---|---:|---|---|",
    ]
    for entry in sorted(entries, key=lambda item: (str(item.get("published_date", "")), str(item.get("title", "")))):
        local = str(entry.get("local_path") or "")
        if local:
            local_path = Path(local)
            try:
                index_relative = local_path.relative_to("原始资料")
            except ValueError:
                index_relative = local_path
            local_link = f"[{local_path.name}]({urllib.parse.quote(index_relative.as_posix(), safe='/')})"
        else:
            local_link = "未归档"
        official = str(entry.get("official_url") or "")
        official_link = f"[官方/原始链接]({official})" if official else "未披露"
        used_by = "、".join(entry.get("used_by", []))
        digest = str(entry.get("sha256") or "")
        rows.append(
            "| "
            + " | ".join(
                (
                    md_escape(entry.get("source_id")),
                    md_escape(entry.get("title")),
                    md_escape(f"{entry.get('document_type', '')} / {entry.get('period', '')}"),
                    md_escape(entry.get("published_date")),
                    local_link,
                    official_link,
                    md_escape(digest[:16] + "…" if digest else "未生成"),
                    md_escape(entry.get("pages")),
                    md_escape(used_by),
                    md_escape(entry.get("status")),
                )
            )
            + " |"
        )
    index_path = report_dir / "原始资料" / "资料索引.md"
    atomic_write_text(index_path, "\n".join(rows) + "\n")
    return index_path


def repair_manifest_dates(report_dir: Path, entries: list[dict[str, object]]) -> int:
    repaired = 0
    for entry in entries:
        used_by = entry.get("used_by", [])
        fallback_candidates = dates_in_text(str(used_by[0])) if used_by else []
        fallback = fallback_candidates[-1] if fallback_candidates else str(entry.get("published_date") or "日期待核验")
        override = str(entry.get("date_override") or "")
        new_date = override if re.fullmatch(r"20\d{6}", override) else infer_date(str(entry.get("official_url") or ""), fallback)
        old_date = str(entry.get("published_date") or "")
        if new_date == old_date or not re.fullmatch(r"20\d{6}", new_date):
            continue
        local = str(entry.get("local_path") or "")
        if local:
            old_path = report_dir / local
            if old_path.exists():
                new_name = old_path.name
                if old_date and new_name.startswith(old_date + "_"):
                    new_name = new_date + new_name[len(old_date):]
                else:
                    new_name = new_date + "_" + new_name
                new_path = report_dir / "原始资料" / new_date[:4] / new_name
                new_path.parent.mkdir(parents=True, exist_ok=True)
                if new_path.exists() and new_path != old_path:
                    digest = str(entry.get("sha256") or "")[:8]
                    new_path = new_path.with_name(f"{new_path.stem}_{digest}{new_path.suffix}")
                os.replace(old_path, new_path)
                entry["local_path"] = new_path.relative_to(report_dir).as_posix()
        entry["published_date"] = new_date
        source_id = str(entry.get("source_id") or "")
        if source_id.startswith("SRC-"):
            digest = str(entry.get("sha256") or "")[:8]
            entry["source_id"] = f"SRC-{new_date}-{digest}"
        repaired += 1
    return repaired


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive official PDF disclosures cited by fundamental-review Markdown files.")
    parser.add_argument("report_dir", type=Path, help="Company 基本面分析 directory.")
    parser.add_argument("reports", nargs="*", type=Path, help="Markdown reports. Defaults to dated reports in report_dir.")
    parser.add_argument(
        "--add-url", action="append", default=[], metavar="LABEL=URL",
        help="Archive an additional verified PDF URL, typically an accessible fallback mirror.",
    )
    parser.add_argument("--used-by", default="历史资料回补", help="Usage label for --add-url entries.")
    parser.add_argument(
        "--override-date", action="append", default=[], metavar="SOURCE_ID=YYYYMMDD",
        help="Override an archived source's public announcement date when a mirror path uses a different file date.",
    )
    parser.add_argument("--index-only", action="store_true", help="Rebuild 资料索引.md from the manifest without downloading.")
    parser.add_argument("--timeout", type=int, default=45, help="Download timeout per PDF in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_dir = args.report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    reports = [path.resolve() for path in args.reports]
    if not reports and not args.index_only:
        reports = sorted(
            path
            for path in report_dir.glob("*.md")
            if "研究轨迹" not in path.name and "资料索引" not in path.name and "_最新" not in path.name
        )

    state_dir = report_dir / ".research"
    manifest_path = state_dir / "sources.json"
    manifest = load_manifest(manifest_path)
    entries = manifest["sources"]
    counts = {"archived": 0, "reused": 0, "deduplicated": 0, "failed": 0, "candidates": 0}

    for report in reports:
        if not report.exists():
            continue
        seen_urls: set[str] = set()
        for label, url in collect_links(report):
            if url in seen_urls:
                continue
            seen_urls.add(url)
            counts["candidates"] += 1
            result = archive_link(report_dir, report, label, url, entries, args.timeout)
            counts[result] += 1

    supplemental_report = report_dir / args.used_by
    for item in ([] if args.index_only else args.add_url):
        if "=" not in item:
            raise SystemExit(f"--add-url 格式错误，应为 LABEL=URL：{item}")
        label, url = item.split("=", 1)
        if not is_pdf_candidate(url):
            raise SystemExit(f"--add-url 不是可识别的 PDF URL：{url}")
        counts["candidates"] += 1
        result = archive_link(report_dir, supplemental_report, label.strip(), url.strip(), entries, args.timeout)
        counts[result] += 1

    for item in args.override_date:
        if "=" not in item:
            raise SystemExit(f"--override-date 格式错误，应为 SOURCE_ID=YYYYMMDD：{item}")
        source_id, date_value = item.split("=", 1)
        if not re.fullmatch(r"20\d{6}", date_value) or not dates_in_text(date_value):
            raise SystemExit(f"--override-date 日期无效：{date_value}")
        entry = next((row for row in entries if row.get("source_id") == source_id), None)
        if entry is None:
            raise SystemExit(f"--override-date 未找到资料编号：{source_id}")
        entry["date_override"] = date_value

    repaired_dates = repair_manifest_dates(report_dir, entries)
    save_manifest(manifest_path, manifest)
    index_path = write_index(report_dir, entries)
    print(f"资料索引: {index_path}")
    print(
        "候选PDF: {candidates} | 新归档: {archived} | 已存在: {reused} | 内容去重: {deduplicated} | 失败: {failed}".format(
            **counts
        )
    )
    if repaired_dates:
        print(f"修复资料日期: {repaired_dates}")
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
