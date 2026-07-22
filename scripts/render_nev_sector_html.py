#!/usr/bin/env python3
"""Render the sector-cycle Markdown with the proven table parser from the stock-review skill."""

from __future__ import annotations

import argparse
import html
import importlib.util
import pathlib
import re
import sys


SKILL_RENDERER = pathlib.Path(
    "/Users/superman/Mine/space/ai/codex-skills/fundamental-stock-review/scripts/render_fundamental_html.py"
)


def load_renderer():
    spec = importlib.util.spec_from_file_location("fundamental_renderer", SKILL_RENDERER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    original = mod.inline_md

    def inline_with_breaks(text: str) -> str:
        return original(text).replace("&lt;br&gt;", "<br>")

    mod.inline_md = inline_with_breaks
    return mod


CSS = r"""
:root{--ink:#16202a;--muted:#627181;--line:#d9e1e8;--soft:#f5f8fa;--brand:#0b6b57;--accent:#d99b27;--down:#a43a3a;--up:#087f5b}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#edf2f4;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;line-height:1.65}
.page{max-width:1500px;margin:0 auto;background:#fff;min-height:100vh;box-shadow:0 0 34px rgba(28,47,60,.12)}
.hero{padding:48px 58px 38px;background:linear-gradient(135deg,#0d5549,#173d4b 68%,#1e2933);color:#fff;border-bottom:5px solid var(--accent)}
.eyebrow{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#bfe2d9}.hero h1{max-width:980px;font-size:42px;line-height:1.18;margin:12px 0 16px}.hero p{max-width:1030px;color:#d7e8e4;margin:0}.hero .meta{margin-top:20px;font-size:13px;color:#b7cbc7}
.layout{display:grid;grid-template-columns:250px minmax(0,1fr);gap:0}.toc{position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto;padding:26px 18px;border-right:1px solid var(--line);background:#fbfcfd}.toc strong{display:block;margin:0 8px 12px;color:#24414c}.toc a{display:block;padding:7px 9px;border-radius:7px;color:#4d5f69;text-decoration:none;font-size:13px}.toc a:hover{background:#e8f3f0;color:var(--brand)}.toc .n{display:inline-block;width:28px;color:#a37820;font-variant-numeric:tabular-nums}
main{min-width:0;padding:34px 42px 70px}section{margin:0 0 34px;scroll-margin-top:18px}.sec{font-size:27px;line-height:1.25;margin:0 0 18px;padding:14px 0 10px;border-bottom:2px solid #193f49}.sec .num{display:inline-flex;align-items:center;justify-content:center;min-width:40px;height:30px;margin-right:12px;border-radius:6px;background:#e2f0ed;color:var(--brand);font-size:14px}.sub{font-size:18px;margin:26px 0 10px;color:#24414c}p{margin:9px 0 15px}blockquote{margin:0}strong{color:#153e47}code{background:#eef2f4;padding:1px 5px;border-radius:4px}
.tbl-scroll{overflow:auto;margin:14px 0 24px;border:1px solid var(--line);border-radius:9px;box-shadow:0 3px 12px rgba(35,55,65,.05)}table{border-collapse:separate;border-spacing:0;min-width:100%;font-size:12.5px;line-height:1.42}th,td{padding:9px 10px;border-right:1px solid #e3e8ec;border-bottom:1px solid #e3e8ec;vertical-align:top;min-width:86px}thead th{position:sticky;top:0;background:#173f49;color:#fff;text-align:left;z-index:1}tbody th{position:sticky;left:0;background:#f8fafb;z-index:0;text-align:left;min-width:118px}tbody tr:nth-child(even) td{background:#fbfcfd}tr:last-child td,tr:last-child th{border-bottom:0}th:last-child,td:last-child{border-right:0}td.up{color:var(--up)}td.down{color:var(--down)}td.muted{color:var(--muted)}a{color:#0a6b84;text-decoration:none}a:hover{text-decoration:underline}ul,ol{padding-left:24px}li{margin:6px 0}
.foot{padding:22px 42px;background:#162a33;color:#b8c6cb;font-size:12px}
@media(max-width:900px){.hero{padding:32px 24px}.hero h1{font-size:30px}.layout{display:block}.toc{position:relative;max-height:none;border-right:0;border-bottom:1px solid var(--line)}main{padding:26px 20px}.sec{font-size:23px}}
@media print{body{background:#fff}.page{box-shadow:none}.toc{display:none}.layout{display:block}main{padding:22px}.hero{padding:28px 34px;color:#000;background:#fff;border-bottom:3px solid #000}.hero p,.hero .meta,.eyebrow{color:#333}.tbl-scroll{overflow:visible;box-shadow:none}thead th{position:static;background:#e8ecef;color:#000}tbody th{position:static}a{color:#000}.foot{background:#fff;color:#333}}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("--output-html", required=True)
    args = ap.parse_args()
    md_path = pathlib.Path(args.markdown).resolve()
    out_path = pathlib.Path(args.output_html).resolve()
    markdown = md_path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", markdown, re.M)
    title = title_match.group(1).strip() if title_match else "A股新能源周期复盘"
    renderer = load_renderer()
    rendered = renderer.render_markdown(markdown)
    toc = "\n".join(
        f'<a href="#{html.escape(sid)}"><span class="n">{html.escape(str(num))}</span>{html.escape(text)}</a>'
        for sid, num, text in rendered.toc
    )
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body><div class="page">
<header class="hero"><div class="eyebrow">BUY-SIDE SECTOR CYCLE REVIEW · A-SHARE NEW ENERGY</div><h1>{html.escape(title)}</h1>
<p>把产业需求、产品价格、资本开支、逐季财务、历史估值与公告后超额收益放在同一条时间线上，区分事实、代理指标与分析判断。</p>
<div class="meta">执行日期 2026-07-23 · 行情截至 2026-07-22 · 主研究窗 2021-01-04 至 2023-12-29</div></header>
<div class="layout"><nav class="toc"><strong>报告目录</strong>{toc}</nav><main>{rendered.html}</main></div>
<footer class="foot">本报告用于历史复盘与研究框架总结，不构成直接买卖建议。数据口径、代理指标与无法验证部分见“研究边界与信息边界”。</footer>
</div></body></html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    print(f"HTML: {out_path}")


if __name__ == "__main__":
    main()
