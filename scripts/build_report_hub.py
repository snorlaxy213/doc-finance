#!/usr/bin/env python3
"""Build the public financial-report hub without changing report sources."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / 'config' / 'publication-policy.json'
SITE_SOURCE = REPO_ROOT / 'hub'
REPORTS_ROOT = REPO_ROOT / 'reports'
DEFAULT_OUTPUT = REPO_ROOT / 'report-hub-build'
BASIC_ANALYSIS_DIR = '基本面分析'
CODE_PATTERN = re.compile(r'^\d{6}$')
TITLE_PATTERN = re.compile(r'<title[^>]*>(.*?)</title>', re.IGNORECASE | re.DOTALL)
TAG_PATTERN = re.compile(r'<[^>]+>')
SCRIPT_STYLE_PATTERN = re.compile(r'<(script|style)\b[^>]*>.*?</\1\s*>', re.IGNORECASE | re.DOTALL)


class BuildError(Exception):
    """Raised when a policy or output configuration is unsafe or invalid."""


def load_policy() -> dict[str, Any]:
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise BuildError(f'找不到发布策略文件：{POLICY_PATH}') from error
    except json.JSONDecodeError as error:
        raise BuildError(f'发布策略不是合法 JSON：{error}') from error

    publication = policy.get('publication')
    if not isinstance(publication, dict) or publication.get('access_mode') != 'public':
        raise BuildError('仅允许明确确认 access_mode 为 public 的策略进行公开构建。')

    codes = policy.get('allowed_report_codes')
    if not isinstance(codes, list) or not codes:
        raise BuildError('allowed_report_codes 必须是非空白名单。')
    if len(codes) != len(set(codes)) or any(not isinstance(code, str) or not CODE_PATTERN.fullmatch(code) for code in codes):
        raise BuildError('allowed_report_codes 只能包含不重复的六位股票代码。')
    if policy.get('required_filename_suffix') != '_基本面分析_最新.html':
        raise BuildError('公开构建只允许 *_基本面分析_最新.html。')
    return policy


def resolve_output(value: str) -> Path:
    output = Path(value).resolve()
    try:
        output.relative_to(REPO_ROOT)
    except ValueError as error:
        raise BuildError('输出目录必须位于仓库内，避免误删仓库外的文件。') from error
    if output == REPO_ROOT:
        raise BuildError('输出目录不能是仓库根目录。')
    return output


def clean_output(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)


def plain_text(raw_html: str) -> str:
    without_code = SCRIPT_STYLE_PATTERN.sub(' ', raw_html)
    without_tags = TAG_PATTERN.sub(' ', without_code)
    return re.sub(r'\s+', ' ', html.unescape(without_tags)).strip()


def extract_title(raw_html: str, fallback: str) -> str:
    match = TITLE_PATTERN.search(raw_html)
    if not match:
        return fallback
    title = re.sub(r'\s+', ' ', html.unescape(TAG_PATTERN.sub('', match.group(1)))).strip()
    return title or fallback


def inject_reader_chrome(raw_html: str, disclaimer: str) -> str:
    """Add public-site navigation to the staged copy only; source reports stay untouched."""
    reader_bar = f'''\n<aside aria-label="报告中心导航" style="margin:32px auto 20px;max-width:1600px;padding:12px 18px;border:1px solid #d8dee7;border-radius:6px;background:#f7f9fc;color:#46546a;font:14px/1.6 system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">\n  <strong style="color:#1f3a5f;">公开报告中心</strong>\n  <span style="margin:0 8px;">·</span><a href="../../index.html" style="color:#1f3a5f;">返回报告目录</a>\n  <span style="margin:0 8px;">·</span><a href="../../portfolio/index.html" style="color:#1f3a5f;">持仓复盘</a>\n  <span style="margin:0 8px;">·</span><a href="../../index.html#disclaimer" style="color:#1f3a5f;">免责声明</a>\n  <div style="margin-top:5px;font-size:12px;">{html.escape(disclaimer)}</div>\n</aside>\n'''
    body_end = re.search(r'</body\s*>', raw_html, flags=re.IGNORECASE)
    if body_end:
        return f'{raw_html[:body_end.start()]}{reader_bar}{raw_html[body_end.start():]}'
    return f'{raw_html}{reader_bar}'


def report_candidates(policy: dict[str, Any]) -> list[tuple[str, Path]]:
    excluded_segments = set(policy['excluded_path_segments'])
    excluded_terms = tuple(policy['excluded_filename_terms'])
    suffix = policy['required_filename_suffix']
    candidates: list[tuple[str, Path]] = []

    for code in policy['allowed_report_codes']:
        source_dir = REPORTS_ROOT / code / BASIC_ANALYSIS_DIR
        if not source_dir.is_dir():
            print(f'[跳过] {code}: 未找到目录 {source_dir.relative_to(REPO_ROOT)}')
            continue
        for report in sorted(source_dir.glob(f'*{suffix}')):
            relative_parts = report.relative_to(REPO_ROOT).parts
            if any(segment in excluded_segments for segment in relative_parts):
                continue
            if any(term in report.name for term in excluded_terms):
                continue
            candidates.append((code, report))

    return candidates


def copy_site_shell(output: Path) -> None:
    if not SITE_SOURCE.is_dir():
        raise BuildError(f'找不到站点模板目录：{SITE_SOURCE}')
    shutil.copytree(SITE_SOURCE, output, dirs_exist_ok=True)


def build_catalog(policy: dict[str, Any], output: Path) -> dict[str, Any]:
    disclaimer = policy['financial_disclaimer']
    items: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for code, source in report_candidates(policy):
        try:
            raw_html = source.read_text(encoding='utf-8')
            title = extract_title(raw_html, source.stem)
            body_text = plain_text(raw_html)
            if not body_text:
                raise BuildError('HTML 中未提取到可检索文本')

            target = output / 'reports' / code / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(inject_reader_chrome(raw_html, disclaimer), encoding='utf-8')
            stat = source.stat()
            source_path = source.relative_to(REPO_ROOT).as_posix()
            modified_at = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec='seconds')
            summary = body_text[:260].rstrip('，。；、 ') + ('…' if len(body_text) > 260 else '')
            items.append(
                {
                    'id': code,
                    'title': title,
                    'code': code,
                    'root': 'reports',
                    'rootLabel': '个股基本面分析',
                    'format': 'HTML',
                    'version': '最新',
                    'sourcePath': source_path,
                    'href': f'reports/{code}/index.html',
                    'modifiedAt': modified_at,
                    'modifiedDate': modified_at[:10],
                    'summary': summary,
                    'searchText': f'{title} {code} {source_path} {body_text}'.lower(),
                }
            )
        except (OSError, UnicodeError, BuildError) as error:
            skipped.append({'code': code, 'sourcePath': str(source), 'reason': str(error)})
            print(f'[跳过] {source}: {error}')

    items.sort(key=lambda item: (item['modifiedAt'], item['code']), reverse=True)
    return {
        'generatedAt': datetime.now().astimezone().isoformat(timespec='seconds'),
        'policy': {
            'accessMode': policy['publication']['access_mode'],
            'includedRoot': policy['publication']['included_root'],
            'includedVariant': policy['publication']['included_variant'],
        },
        'disclaimer': disclaimer,
        'items': items,
        'skipped': skipped,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def verify_output(output: Path) -> dict[str, Any]:
    catalog_path = output / 'data' / 'catalog.json'
    portfolio_root = output / 'portfolio'
    portfolio_files = [portfolio_root / 'index.html', portfolio_root / 'portfolio.js', portfolio_root / 'portfolio.css', portfolio_root / 'portfolio-config.js']
    if not (output / 'index.html').is_file() or not catalog_path.is_file():
        raise BuildError('构建产物缺少首页或目录索引。')
    if any(not path.is_file() for path in portfolio_files):
        raise BuildError('构建产物缺少持仓入口所需的静态文件。')
    private_artifacts = [portfolio_root / 'portfolio-seed.local.json', portfolio_root / '.env.portfolio', output / 'portfolio-backups']
    if any(path.exists() for path in private_artifacts):
        raise BuildError('检测到不应发布的私有持仓种子、凭据或备份文件。')
    public_config = (portfolio_root / 'portfolio-config.js').read_text(encoding='utf-8')
    if 'PORTFOLIO_SUPABASE_SERVICE_ROLE_KEY' in public_config or 'your-service-role-key' in public_config:
        raise BuildError('持仓公开配置中包含 service-role key 标记。')
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    prohibited = ('草稿', '研究轨迹', '.research', '原始资料', '_drafts')
    for item in catalog.get('items', []):
        if not item['href'].endswith('/index.html') or not (output / item['href']).is_file():
            raise BuildError(f"目录链接缺失：{item.get('href')}")
        searchable = f"{item.get('title', '')} {item.get('sourcePath', '')}"
        if any(term in searchable for term in prohibited):
            raise BuildError(f'检测到不应发布的目录条目：{item.get("sourcePath")}')
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description='构建仅包含白名单最新 HTML 报告的 GitHub Pages 站点。')
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT), help='仓库内的静态站输出目录。')
    parser.add_argument('--clean', action='store_true', help='构建前清空输出目录。')
    parser.add_argument('--verify-only', action='store_true', help='只验证已有输出，不生成文件。')
    args = parser.parse_args()

    try:
        output = resolve_output(args.output)
        if args.verify_only:
            catalog = verify_output(output)
            print(f"验证通过：{len(catalog['items'])} 份公开报告，输出目录：{output}")
            return 0

        policy = load_policy()
        if args.clean:
            clean_output(output)
        else:
            output.mkdir(parents=True, exist_ok=True)
        copy_site_shell(output)
        catalog = build_catalog(policy, output)
        write_json(output / 'data' / 'catalog.json', catalog)
        write_json(output / 'data' / 'build-report.json', {'included': len(catalog['items']), 'skipped': catalog['skipped']})
        verify_output(output)
        print(f"构建完成：{len(catalog['items'])} 份公开报告，{len(catalog['skipped'])} 份跳过，输出目录：{output}")
        return 0
    except BuildError as error:
        print(f'构建失败：{error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
