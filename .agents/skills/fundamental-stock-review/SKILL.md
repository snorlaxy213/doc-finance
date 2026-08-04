---
name: fundamental-stock-review
description: Analyze and continuously update a listed company's fundamentals, produce a conditional current-position trade decision with position sizing and risk controls, preserve immutable Markdown/HTML snapshots and conclusion history, and archive cited official PDF filings. Covers business quality, financial quality, valuation, current price/volume position, buy/wait/hold/reduce/exit research actions, orders/backlog, ownership, negative news, and financial-fraud risk flags. Use when the user asks for 基本面分析, 财报分析, 财务质量分析, 股票深度复盘, 当前是否是买点, 现在能不能买, 买卖建议, 仓位建议, 止损点, 后续更新, 业绩预告跟踪, 订单跟踪, 订单消息整理, 中标分析, 重大合同, backlog, 合同负债, 客户采购, 招投标信息, 是否财务造假, or wants to evaluate a stock using valuation, growth, profitability, cash flow, ownership, institutional participation, market share, loss, or negative-news indicators.
---

# Fundamental Stock Review

## Core Rules

- Answer in Simplified Chinese unless the user asks otherwise.
- Use a professional investment-research tone. Provide conditional research actions rather than guaranteed-return language or certainty disguised as a personalized instruction.
- Always add the current-position trade-decision layer. Use the user's stated risk parameters; otherwise apply `项目级个股交易决策默认值` from the repository-root `AGENTS.md`. Read [references/trade-decision-framework.md](references/trade-decision-framework.md) before collecting price/volume data or drafting that decision.
- Treat fundamentals as the answer to whether the company is investable and price/volume structure as the answer to whether the current position is actionable. Do not infer a buy point from low PE/PB alone.
- If recent reliable OHLCV, a reference entry price, or valuation-upside evidence is unavailable, output `等待 / 无法判断当前买点` and identify the missing evidence; never fabricate an entry range, stop price, or target.
- Verify current, time-sensitive facts before concluding: ticker/name mapping, latest filings, latest price/market-cap data, major announcements, regulatory actions, and recent negative news.
- Check whether the company issued an official earnings forecast, profit alert, profit warning, forecast revision, 盈喜, or 盈警 during the 30 calendar days ending on the report execution date. Treat forecast figures as unaudited and keep them separate from reported financial statements.
- Separate confirmed disclosure from market rumor or narrative. Label uncertain items as 信息边界.
- For orders, contracts, and bidding information, distinguish 招标, 中标候选人, 中标公告, 合同签署, 框架协议, delivered revenue, and unverified market rumor.
- Treat negative governance, audit, regulatory, or cash-flow issues as possible conclusion downgrades even when growth and valuation look attractive.
- Do not infer financial fraud from a single indicator. Present it as fraud-risk screening unless there is confirmed regulatory, audit, or legal evidence.
- Treat a company review as a continuous research record, not an isolated rewrite. Before updating an existing company, read the stable latest report, the research timeline, and unresolved tracking items.
- Preserve every dated Markdown/HTML pair as an immutable snapshot. Never overwrite, edit, or delete a dated historical report during a later update.
- When a previous report exists, explicitly distinguish newly confirmed facts, invalidated assumptions, unchanged views, and conclusion changes. Do not silently change conclusion wording or reset the tracking list.
- Archive every official PDF filing materially cited by the report, prefer company/exchange/statutory-disclosure originals, verify the file, deduplicate by SHA-256, and cite the verified local relative path. Keep the official URL in the source index.
- Read [references/versioning-and-sources.md](references/versioning-and-sources.md) before updating an existing company, publishing report artifacts, migrating historical reports, or archiving source PDFs.

## Review Gate

After evidence collection and before rendering or publishing, invoke `$financial-analysis-reviewer` as a read-only child reviewer. Pass a compact evidence packet containing the company/ticker, analysis date, report periods, draft conclusion, key figures, source paths, unresolved items, changes from the prior report, trade action, market-data date, reference/entry price, target position, stop, upside basis, reward/risk, and fundamental invalidation conditions.

- Use `通过 / 需要修订 / 阻断` as the review result.
- Do not publish when the result is `阻断`; correct the evidence or lower the conclusion strength, then review again.
- Keep this Skill responsible for the final conclusion, immutable snapshots, HTML generation, PDF archiving, research timeline, and publication. The reviewer may flag issues but must not edit these artifacts.
- Re-run the reviewer only when a revision changes the core conclusion, rating, risk level, or report period.

## Output Artifacts

By default, produce both a Markdown report and a standalone HTML report unless the user explicitly asks for chat-only output.

Use this file layout when working inside the user's `doc-finance` workspace:

```text
/Users/superman/Mine/space/ai/doc-finance/reports/<股票代码>/基本面分析/
```

Use these filename patterns:

```text
<公司简称>_<股票代码>_基本面分析_<YYYYMMDD_HHMMSS>.md
<公司简称>_<股票代码>_基本面分析_<YYYYMMDD_HHMMSS>.html
```

Also maintain these stable artifacts for each company:

```text
<公司简称>_<股票代码>_基本面分析_最新.md
<公司简称>_<股票代码>_基本面分析_最新.html
<公司简称>_<股票代码>_研究轨迹.md
<公司简称>_<股票代码>_研究轨迹.html
原始资料/<YYYY>/<公告日期>_<报告期>_<文档类型>_<公告标识>.pdf
原始资料/资料索引.md
.research/state.yaml
```

Rules:

- Use the current date and time as `YYYYMMDD_HHMMSS` for new snapshots. Existing date-only files remain valid historical snapshots and must not be renamed merely for consistency.
- If the user provides a different report root, use that root. Otherwise, use `/Users/superman/Mine/space/ai/doc-finance/reports` when available; in other workspaces, use `reports/`.
- Use baseline mode when no prior report exists. Use incremental-update mode when a prior report exists. Use full-rebuild mode for an annual report, accounting restatement, major business transformation, or an explicit user request; even a full rebuild must compare with the prior conclusion.
- In incremental-update mode, carry forward still-valid confirmed facts, re-check time-sensitive facts, update affected sections, and retain unresolved tracking items. Do not rewrite unchanged analysis merely for stylistic variation.
- Save the Markdown report first, using the fixed output structure below and valid GitHub-Flavored Markdown tables.
- Generate the HTML from the same Markdown using `scripts/render_fundamental_html.py`; do not hand-maintain a separate HTML narrative that can drift from the Markdown.
- Archive official PDF evidence with `scripts/archive_disclosures.py` before final publication, then use local links such as `原始资料/2026/<file>.pdf` in the Markdown. Do not rewrite old reports solely to replace their remote links.
- Publish new reports with `scripts/publish_fundamental_review.py`; it creates the immutable timestamped snapshot, atomically refreshes the stable latest pair, and rebuilds the research timeline and state index.
- Start the Markdown body with `### 1. 核心财务指标` immediately after the H1 title. Do not place a free-standing conclusion, executive summary, background, or time-range paragraph between the title and section 1.
- Keep the HTML self-contained: inline CSS/JS, no external assets, no network font or CDN dependency.
- Do not fabricate visualizations. If chart data is not explicitly present in the report tables, let the HTML render tables and summary cards only.
- After rendering, verify that the exact `一句话结论` appears once in the HTML: in the top `结论速览`, not again in the main body.
- Final response must include the absolute paths of both the Markdown and HTML files.

Example command after writing the Markdown file:

```bash
python3 /Users/superman/Mine/space/ai/doc-finance/.agents/skills/fundamental-stock-review/scripts/render_fundamental_html.py \
  /absolute/path/to/<公司简称>_<股票代码>_基本面分析_<YYYYMMDD_HHMMSS>.md \
  --output-html /absolute/path/to/<公司简称>_<股票代码>_基本面分析_<YYYYMMDD_HHMMSS>.html
```

Preferred publication command for a completed report:

```bash
python3 /Users/superman/Mine/space/ai/doc-finance/.agents/skills/fundamental-stock-review/scripts/publish_fundamental_review.py \
  /absolute/path/to/completed-report.md \
  --reports-root /Users/superman/Mine/space/ai/doc-finance/reports
```

The renderer's `--copy-md` flow remains available for legacy one-off rendering. For continuous reports, always use `publish_fundamental_review.py` so the latest pair, timeline, and state stay synchronized.

## Data Collection Checklist

Collect the latest available data from public filings, exchange announcements, financial data providers, and credible news sources:

- Current valuation snapshot: latest price date, closing price, total market cap, free-float market cap, PE, PB, PS, dividend yield if relevant. Treat these as latest point-in-time market data, not historical financial-statement metrics.
- Trade-decision inputs: sufficiently recent daily/weekly OHLCV, trend-health label, identifiable support/invalidation level, current price versus entry range, valuation-derived upside, existing-position status when disclosed, requested position cap, and requested stop. Keep market facts date-stamped.
- Recent financial forecast: official announcement date, forecast period, forecast range or midpoint, prior-year comparable amount, cumulative YoY, forecast revision, revenue if disclosed, attributable net profit, deducted non-recurring net profit, EPS if disclosed, non-recurring contribution, stated drivers, and whether the same-period formal report has subsequently been released.
- Growth: revenue, net profit, deducted non-recurring net profit, YoY growth, EPS, 3-year trend, and whether growth comes from core-business volume, price, market-share gains, acquisitions, or non-recurring items.
- Profitability: gross margin, deducted net margin, net margin, ROE, ROIC if available, margin drivers, and peer comparison.
- Cash-flow quality: operating cash flow, operating cash flow / net profit, cash received from sales / revenue, free cash flow, and whether cash flow keeps up with profit.
- Capital allocation and asset efficiency: capital expenditure, capex / revenue, capex efficiency, construction in progress, depreciation pressure, and free-cash-flow status.
- Balance-sheet quality: accounts receivable, inventory, contract assets, prepayments, other receivables, goodwill, construction in progress, interest-bearing debt, cash, asset-liability ratio, inventory turnover and impairment if relevant.
- Ownership and governance: top-ten shareholder concentration, controller stake, pledge ratio, reduction plans, related-party transactions, guarantees, fund occupation.
- Institutional participation: number and type of institutions, public funds, social security funds, QFII, insurance funds, northbound capital where applicable.
- Business position: main products, segment revenue and gross margin for the past two years, market share, customer structure, supplier structure, competitive advantages, industry cycle.
- Research and communication information: investor-relations records, earnings-call notes, exchange interactive Q&A, management discussion, disclosed order/backlog information, capacity expansion progress, and customer or product updates.
- Order and demand evidence: exchange announcements for major contracts and daily operating contracts; public procurement, public-resource trading, industry tender platforms, and customer-side procurement announcements; company IR news, investor records, earnings calls, and interactive Q&A; financial-statement signals such as contract liabilities, inventory, accounts receivable, operating cash flow, capacity utilization, and remaining performance obligations; customs, bill-of-lading, or supply-chain data for export-oriented companies when available.
- Risk events: losses, ST/delisting risk, audit opinion, audit firm change, annual-report inquiry letters, regulatory penalties, litigation, negative news, customer/supplier authenticity disputes.

## Analysis Logic

Use this priority order:

1. Put key data first: start with the latest valuation snapshot; then show an official financial forecast issued within the latest 30 calendar days, including cumulative YoY and implied latest-quarter YoY/QoQ when calculable; then separate reported current-year interim metrics from recent annual metrics. Never mix forecast figures with reported results.
2. Business first: decide whether the company has a durable business, industry tailwind, and defensible product position.
3. Profit second: judge whether revenue, net profit, deducted net profit, EPS, margin, ROE, and segment profitability form a coherent trend.
4. Cash flow third: verify whether profit converts into cash. Strong profit with weak operating cash flow is a major warning.
5. Balance sheet fourth: identify whether profit is being stored in receivables, inventory, prepayments, other receivables, goodwill, or construction in progress.
6. Cross-check trend quality with peers and company communications: compare multiple periods, peer metrics, management discussion, investor communication, orders, capacity, and customer progress.
7. Treat orders as demand evidence, not profit evidence by default: verify order status, amount attribution, fulfillment period, revenue recognition timing, margin profile, customer credit quality, and payment terms before upgrading the conclusion.
8. Valuation fifth: compare valuation with growth quality, industry cycle, and peers. Low PE is not automatically cheap; high PE needs durable growth and certainty.
9. Governance and negative news last: apply risk downgrades for audit, regulatory, pledge, reduction, related-party, litigation, or authenticity issues.

## Order and Demand Verification

When order, contract, bidding, backlog, or demand-tracking information is relevant, structure evidence before interpretation:

| 日期 | 来源与链接 | 项目/订单名称 | 客户/采购方 | 产品/服务 | 金额 | 状态 | 履约周期 | 是否公司正式公告 | 对收入影响 | 可信度 |
|---|---|---|---|---|---:|---|---|---|---|---|

Use these rules:

- Do not treat a tender opportunity or 中标候选人公示 as a confirmed signed order.
- Treat framework agreements, strategic cooperation, letters of intent, and memoranda as low-certainty unless concrete purchase quantities, prices, or binding purchase obligations are disclosed.
- For consortium wins, identify the company's attributable scope and amount; if not disclosed, label it as 未披露 instead of using the full project amount.
- Compare order amount with latest annual revenue and segment revenue; state whether it is financially material.
- Map fulfillment period to likely revenue recognition windows instead of assuming one-time revenue.
- Cross-check order growth with contract liabilities, inventory, capacity utilization, accounts receivable, and operating cash flow.
- Downgrade confidence when order growth is accompanied by faster receivable/contract-asset growth, weak cash collection, abnormal inventory buildup, or vague customer disclosure.

## Fraud-Risk Red Flags

Flag fraud/accounting-quality risk when multiple items appear together:

- Net profit grows while operating cash flow stays weak or negative for multiple periods.
- Accounts receivable grows much faster than revenue.
- Inventory grows much faster than revenue, or inventory impairment is insufficient.
- Gross margin is far above peers without clear product, technology, or customer explanation.
- Deducted non-recurring net profit is materially weaker than reported net profit.
- Prepayments, other receivables, construction in progress, or goodwill expands abnormally.
- Audit firm changes frequently, audit opinion is non-standard, or key audit matters are severe.
- Controller has high pledge ratio, frequent reductions, fund occupation, or abnormal guarantees.
- Top customers or suppliers are highly concentrated, vaguely disclosed, or publicly disputed.
- Exchange inquiries, regulatory penalties, litigation, media investigations, or short-seller-style allegations cluster around financial authenticity.

Classify fraud-risk screening as:

- Low: no material red flags; profit, cash flow, balance sheet, and peer metrics broadly match.
- Medium: 1-2 major red flags or several mild inconsistencies requiring follow-up.
- High: multiple major red flags, especially cash-flow mismatch plus receivable/inventory expansion plus audit/regulatory/governance issues.

## Fixed Output Structure

Always use the following structure. Put the data tables before the narrative conclusion so the reader can first see the financial evidence.

The Markdown must remain renderer-friendly:

- Use `###` for main numbered sections and `####` for subsections.
- Keep tables as normal Markdown pipe tables.
- Keep conclusion labels exactly as `基本面判断`, `财务质量`, `估值状态`, and `财务造假风险初筛` so the HTML renderer can extract summary badges.
- Keep `一句话结论` exactly as a single-line item in section 3. The HTML renderer extracts it into the top `结论速览` and suppresses the duplicate line in the main body.
- Put the report execution date, market-data date, covered financial periods, and historical-data caveats under section 12 `信息边界` as `分析范围`; do not repeat them before section 1.
- Keep the final copyable block in a fenced `text` or `plain` code block so the HTML renderer can show it as `基本面速记`.
- Put `交易决策摘要` inside the final copyable block, after the fundamental note. This makes the decision appear at the existing `基本面速记` HTML location without a renderer change.
- Do not mix latest market valuation data with historical financial-statement tables; the HTML header and KPI cards rely on clean valuation and financial blocks.

### 1. 核心财务指标

Do not mix forecast, interim-report, and annual-report figures in one table. Use four blocks in this order: latest valuation snapshot, latest financial forecast, disclosed current-year interim reports, and recent three-year annual reports. Use `亿元` for money amounts, `元/股` for EPS, and `%` for ratios unless otherwise stated. Use `未披露` or `不适用` when data cannot be confirmed.

#### 1.1 当前估值快照

Show only the latest available market and valuation data above the financial-statement tables. Do not put latest market cap, free-float market cap, PE, PB, or PS inside the multi-period financial tables, because these are latest point-in-time market data and historical same-date values are often unavailable.

| 项目 | 最新数据 | 数据日期/口径 | 解读 |
|---|---:|---|---|
| 收盘价 |  |  | 当前估值计算基础 |
| 总市值 |  |  | 当前整体市值水平 |
| 流通市值 |  |  | 当前可流通股份对应市值 |
| PE |  |  | 与利润增速、行业周期、同行估值匹配度 |
| PB |  |  | 与 ROE、资产质量和行业属性匹配度 |
| PS |  |  | 适用于利润波动或成长阶段公司，需结合毛利率和现金流 |
| 股息率 |  |  | 如适用，结合分红稳定性和现金流质量 |

#### 1.2 最新财务预报与质量解读

Always reserve this subsection so the output structure remains stable.

Trigger and source rules:

- Use the report execution date as the endpoint and look back 30 calendar days, inclusive.
- Include only company or exchange filings: earnings forecasts, profit alerts/warnings, forecast revisions, 盈喜, or 盈警. Do not use broker estimates, media estimates, or market rumor as the core forecast.
- When multiple forecasts or revisions exist for the same period, use the latest revision and explain whether it raised, lowered, narrowed, or widened the previous range.
- When the formal report for the same period has already been released, present a brief `预报兑现检查` comparing forecast and actual instead of presenting the forecast as current guidance.
- When no qualifying official forecast exists, write `近30日未披露新的正式财务预报` and do not create empty forecast tables.
- Mark every forecast as `未经审计`. Do not infer undisclosed revenue, gross margin, operating cash flow, ROE, balance-sheet data, or free cash flow.
- Keep the financial-forecast subsection and the HTML forecast panel limited to forecast facts, derived-quarter calculations, information confidence, and earnings-quality assessment. Do not put the overall valuation, governance, fraud-risk, or comprehensive fundamental conclusion in this panel.

##### 1.2.1 累计业绩预报

| 指标 | 本期预报区间 | 上年同期 | 同比变化 | 预报中枢 | 质量解读 |
|---|---:|---:|---:|---:|---|
| 预报期间 |  | 不适用 | 不适用 | 不适用 | 明确 Q1/H1/Q3/全年及公告日期，注明未经审计 |
| 预报营业收入 |  |  |  |  | 未披露时写未披露，不以利润增速倒推收入 |
| 预报归母净利润 |  |  |  |  | 增长、下滑、扭亏、减亏、转亏或增亏 |
| 预报扣非归母净利润 |  |  |  |  | 是否与归母净利润方向和幅度一致 |
| 预报 EPS |  |  |  |  | 仅在正式公告披露或股本口径可可靠确认时使用 |
| 预计非经常性损益 |  |  |  |  | 资产处置、补贴、投资收益、减值转回等影响 |

Use the company's disclosed YoY where available and cross-check it against the stated prior-year base. Calculate the midpoint only when both lower and upper bounds are disclosed. If the comparison base is zero, negative, or too small for a meaningful percentage, use `扭亏 / 减亏 / 转亏 / 增亏` instead of a mechanical percentage.

##### 1.2.2 隐含最新单季度同比与环比

| 指标 | 隐含本季度区间 | 去年同季度 | 单季同比 | 上一季度 | 单季环比 | 解读 |
|---|---:|---:|---:|---:|---:|---|
| 隐含单季营业收入 |  |  |  |  |  | 仅在累计预报披露收入且前序累计收入已正式披露时计算 |
| 隐含单季归母净利润 |  |  |  |  |  | 判断盈利动能是加速、稳定还是回落 |
| 隐含单季扣非归母净利润 |  |  |  |  |  | 判断主业盈利趋势是否延续 |
| 隐含单季 EPS |  |  |  |  |  | 仅在股本口径可比时计算 |

Calculation rules:

- H1 forecast: implied Q2 = H1 forecast range minus reported Q1; prior-year Q2 = prior-year H1 minus prior-year Q1.
- Q3 cumulative forecast: implied Q3 = Q1-Q3 forecast range minus reported H1; prior-year Q3 = prior-year Q1-Q3 minus prior-year H1.
- Annual forecast: implied Q4 = annual forecast range minus reported Q1-Q3; prior-year Q4 = prior-year annual minus prior-year Q1-Q3.
- Q1 forecast: use the Q1 range directly; compare QoQ with the prior-year Q4 derived from the latest annual and Q3 figures when those figures are comparable.
- For a range forecast `[L, U]` and preceding cumulative actual `A`, calculate the implied quarter as `[L-A, U-A]`. Calculate YoY and QoQ as ranges using both endpoints when the comparison base is positive and meaningful.
- If a comparison base is zero or negative, describe `扭亏 / 减亏 / 转亏 / 增亏` instead of showing a misleading percentage.
- Label all derived quarterly figures as `根据累计预报和已披露财报推算，非公司直接披露`.
- Do not calculate revenue YoY/QoQ when forecast revenue is undisclosed.

After the tables, add `财务预报质量判断` covering:

- Whether attributable and deducted net profit move in the same direction and whether non-recurring items dominate the forecast.
- Whether cumulative YoY and implied latest-quarter YoY/QoQ indicate accelerating, stable, or weakening earnings momentum.
- Whether the forecast range is narrow enough to indicate useful visibility; optionally calculate range width as `(upper bound - lower bound) / midpoint`.
- Whether stated drivers are supported by price, volume, market share, orders, capacity utilization, industry data, or already reported segment results.
- Which important quality indicators remain unavailable, especially revenue, cash flow, receivables, inventory, gross margin, and capital expenditure.
- `信息可信度：高 / 中 / 低`, based on source authority, revision status, range width, and disclosure completeness.
- `盈利质量判断：强 / 中性 / 偏弱 / 无法判断`, based on core-business contribution, deducted-profit consistency, latest-quarter momentum, and non-recurring dependence.

#### 1.3 已披露当年期间财报

Use this block for the current year's already disclosed interim reports only, plus the latest interim report's same period last year. This block is for comparable interim-period analysis, not annual-trend analysis.

Column rules:

- If the latest disclosed report is Q1, use `去年Q1 / 当年Q1`.
- If the latest disclosed report is H1, use `去年H1 / 当年Q1 / 当年H1`.
- If the latest disclosed report is Q3, use `去年Q3 / 当年Q1 / 当年H1 / 当年Q3`.
- If one current-year interim period has not been disclosed or cannot be confirmed, mark it `未披露` or omit that column.
- Do not combine annual periods such as `2024A / 2025A` with interim periods such as `2026Q1` in this table.

| 指标 | 去年同期 | 当年Q1 | 当年H1 | 当年Q3 | 变化解读 |
|---|---:|---:|---:|---:|---|
| 营业收入 |  |  |  |  | 是否来自主业放量、价格提升、市占率提升、并表或一次性因素 |
| 归母净利润 |  |  |  |  | 增速是否与收入、毛利率、费用率匹配 |
| 扣非归母净利润 |  |  |  |  | 是否代表核心经营质量，是否明显弱于归母净利润 |
| 经营现金流净额 |  |  |  |  | 能否跟上净利润，是否存在利润现金含量变弱 |
| 经营现金流/净利润 |  |  |  |  | 利润兑现质量，低于 1 或连续走弱需解释 |
| 自由现金流 |  |  |  |  | 资本开支后是否仍能产生现金，扩产期需说明原因 |
| EPS |  |  |  |  | 每股盈利趋势，结合股本变化看 |
| ROE |  |  |  |  | 盈利能力与资本效率是否维持 |
| 毛利率 |  |  |  |  | 产品结构、价格、成本、竞争格局导致的变化 |
| 扣非净利率 |  |  |  |  | 核心盈利能力是否改善或恶化 |
| 资本开支 |  |  |  |  | 扩产、设备投入、在建工程转固与回报效率 |
| 存货 |  |  |  |  | 是否快于收入增长，结合跌价准备、周转和订单验证 |
| 应收账款/合同资产 |  |  |  |  | 是否快于收入增长，回款压力与客户质量 |
| 总资产 |  |  |  |  | 资产扩张是否有效支撑盈利 |
| 归母净资产 |  |  |  |  | 净资产增长与 ROE 的匹配情况 |

#### 1.4 最近三年年度财报

Use this block for the latest three annual reports, for example `2023A / 2024A / 2025A`. This block should focus on annual trend quality and avoid mixing in quarterly or half-year data.

| 指标 | 前两年 | 前一年 | 最新年度 | 变化解读 |
|---|---:|---:|---:|---|
| 营业收入 |  |  |  | 是否来自主业放量、价格提升、市占率提升、并表或一次性因素 |
| 归母净利润 |  |  |  | 增速是否与收入、毛利率、费用率匹配 |
| 扣非归母净利润 |  |  |  | 是否代表核心经营质量，是否明显弱于归母净利润 |
| 经营现金流净额 |  |  |  | 能否跟上净利润，是否存在利润现金含量变弱 |
| 经营现金流/净利润 |  |  |  | 利润兑现质量，低于 1 或连续走弱需解释 |
| 自由现金流 |  |  |  | 资本开支后是否仍能产生现金，扩产期需说明原因 |
| EPS |  |  |  | 每股盈利趋势，结合股本变化看 |
| ROE |  |  |  | 盈利能力与资本效率是否维持 |
| 毛利率 |  |  |  | 产品结构、价格、成本、竞争格局导致的变化 |
| 扣非净利率 |  |  |  | 核心盈利能力是否改善或恶化 |
| 资本开支 |  |  |  | 扩产、设备投入、在建工程转固与回报效率 |
| 存货 |  |  |  | 是否快于收入增长，结合跌价准备、周转和订单验证 |
| 应收账款/合同资产 |  |  |  | 是否快于收入增长，回款压力与客户质量 |
| 总资产 |  |  |  | 资产扩张是否有效支撑盈利 |
| 归母净资产 |  |  |  | 净资产增长与 ROE 的匹配情况 |

After the table, add a short paragraph named `核心指标综合判断` covering:

- 收入增长是否来自主业放量、份额提升或可持续订单，而不是并表、价格扰动或低质量扩张。
- 毛利率、扣非净利率的变化方向和原因，必要时结合产品结构、原材料、费用率和竞争格局。
- 经营现金流、自由现金流、资本开支效率、存货和应收款是否支持利润真实性与增长质量。
- 至少做多期比对；有可比公司数据时加入同行业比对。
- 纳入公告、交流纪要、调研、互动问答或管理层讨论中的有效信息，并标注信息边界。

### 2. 近两年财报趋势与业务结构

First summarize the latest two years of financial trend, then show segment/business changes. Use annual data when possible; for companies that disclose only half-year or quarterly segment data, clearly label the period and avoid mixing incomparable periods without explanation.

#### 2.1 近两年财报趋势

| 项目 | 前一年 | 最新年度/期间 | 变化 | 解读 |
|---|---:|---:|---:|---|
| 营业收入 |  |  |  | 主业需求、价格、份额、并表或周期影响 |
| 归母净利润 |  |  |  | 利润弹性与费用、减值、投资收益影响 |
| 扣非归母净利润 |  |  |  | 核心经营利润是否同步增长 |
| 毛利率 |  |  |  | 产品结构、价格、成本和竞争格局 |
| 扣非净利率 |  |  |  | 费用率、规模效应、减值和非经常因素 |
| 经营现金流净额 |  |  |  | 回款、应收、存货、票据和预收变化 |
| 自由现金流 |  |  |  | 资本开支后现金剩余或消耗 |
| 存货 |  |  |  | 备货、滞销、订单和跌价准备 |
| 应收账款/合同资产 |  |  |  | 收入质量、账期和客户回款 |

#### 2.2 分业务情况

| 业务 | 前一年收入 | 前一年毛利率 | 最新年度/期间收入 | 最新年度/期间毛利率 | 变化 |
|---|---:|---:|---:|---:|---|
| 业务 1 |  |  |  |  | 收入、毛利率、产品结构、价格或成本变化 |
| 业务 2 |  |  |  |  |  |
| 其他业务 |  |  |  |  |  |

After the table, add `业务结构判断` covering which segments are the real growth engine, which segments drag margins or cash flow, whether new businesses are large enough to matter, and whether disclosed orders/capacity/customer progress supports sustainability.

### 3. 结论摘要

#### 3.1 当前结论

- 一句话结论：用一行综合盈利趋势、财务质量、估值与关键治理风险；不要只复述最新财务预报
- 基本面判断：强 / 中性 / 偏弱 / 高风险
- 财务质量：优秀 / 良好 / 一般 / 存疑
- 估值状态：偏低 / 合理 / 偏高 / 无法判断
- 财务造假风险初筛：低 / 中 / 高
- 核心理由：用 3-5 条说明，不超过一屏

Keep these labels exactly once in this subsection so the renderer can extract them.

#### 3.2 与上次报告相比

When no prior report exists, write `首次建立研究基线，无上次报告可比` and identify the baseline date. Otherwise include:

| 判断维度 | 上次结论 | 本次结论 | 变化级别 | 变化原因与证据 |
|---|---|---|---|---|
| 基本面 |  |  | 不变/微调/上调/下调 |  |
| 财务质量 |  |  | 不变/微调/上调/下调 |  |
| 估值 |  |  | 不变/微调/上调/下调 |  |
| 财务造假风险初筛 |  |  | 不变/微调/上调/下调 |  |

After the table, state `本次触发事件`, `新增确认事实`, `被证伪或弱化的旧假设`, `仍然有效的旧观点`, and `仍待验证事项`. A conclusion may remain unchanged; record that explicitly rather than inventing a change.

#### 3.3 当前位置与交易决策

Apply [references/trade-decision-framework.md](references/trade-decision-framework.md). State the market-data date and distinguish `未持仓` from `已持仓`; if position status is unknown, provide both conditional rows. Output exactly one primary research action from `可以分步买入 / 小仓试错 / 等待 / 持有观察 / 降仓 / 退出`, plus target position, entry/no-chase condition, stop, fundamental invalidation, valuation-upside basis, reward/risk, validity period, confidence, and the most important counterevidence.

Do not output `可以分步买入` unless the fundamental, valuation, technical-position, and reward/risk gates all pass. A `中性` fundamental conclusion, `一般` financial quality, mixed trend, stale price data, or unquantifiable upside cannot support a full 25% target by itself.

### 4. 公司与行业

- 主营业务：
- 主要产品：
- 市场占有率：
- 行业景气度：
- 核心竞争力：
- 主要依赖：单一产品 / 单一客户 / 单一政策 / 无明显集中依赖

### 5. 订单与需求验证

Use this section when the company discloses orders/backlog, the user asks about order tracking, or the business model depends heavily on project awards, government procurement, customer capex cycles, export shipments, or enterprise contracts. If no reliable order data is available, state `未发现可核验订单数据` and explain the information boundary.

| 日期 | 来源与链接 | 项目/订单名称 | 客户/采购方 | 产品/服务 | 金额 | 状态 | 履约周期 | 是否公司正式公告 | 对收入影响 | 可信度 |
|---|---|---|---|---|---:|---|---|---|---|---|
|  |  |  |  |  |  | 招标/中标候选人/中标/已签合同/框架协议 |  | 是/否 |  | 高/中/低 |

- 已披露订单/合同：
- 招投标与客户侧线索：
- 订单状态区分：
- 订单金额与最近年度营收比例：
- 履约周期与收入确认节奏：
- 合同负债/存货/应收/现金流验证：
- 订单趋势判断：改善 / 稳定 / 走弱 / 无法判断
- 信息可信度：高 / 中 / 低

### 6. 财务质量验证

- 利润与现金流匹配：
- 应收账款与营收匹配：
- 存货与营收匹配：
- 资本开支效率与自由现金流：
- 预付款/其他应收款/在建工程/商誉异常：
- 资产负债率与有息负债：
- 综合判断：

### 7. 股东与机构

- 十大股东持股占比：
- 实控人/大股东持股与质押：
- 大股东减持或增持：
- 入驻机构家数：
- 机构类型：
- 治理风险判断：

### 8. 估值与同行对比

- 当前估值：
- 同行业估值对比：
- 同行业收入增速/毛利率/扣非净利率/ROE/现金流质量对比：
- 估值是否匹配成长与财务质量：

### 9. 负面信息与风险排查

- 是否亏损：
- 是否 ST 或退市风险：
- 审计意见：
- 监管问询/处罚：
- 诉讼仲裁：
- 负面新闻：
- 关联交易/客户供应商真实性争议：

### 10. 财务造假风险初筛

- 红旗数量：
- 主要红旗：
- 风险等级：低 / 中 / 高
- 解释：说明这是风险初筛，不是事实定性；只有监管、审计、司法或公司公告确认后才能定性。

### 11. 后续跟踪清单

Carry forward every unresolved item from the prior report. An item can disappear only after it is explicitly marked `已验证`, `已证伪`, or `已关闭`.

| 跟踪事项 | 首次提出 | 上次状态 | 本次证据 | 当前状态 | 下次验证时间/触发条件 |
|---|---|---|---|---|---|
|  |  | 待验证/部分验证/已验证/已证伪/已关闭 |  |  |  |

- 新增订单金额与年初至今累计订单金额：
- 订单金额/上年营收：
- 重点客户复购与新增客户：
- 中标候选人转正式中标/签约情况：
- 合同负债、存货、应收账款和经营现金流变化：
- 触发深度复盘条件：

### 12. 信息边界

- 分析范围：报告执行日、行情日期、覆盖的财务期间、使用的上次报告版本，以及可能削弱历史可比性的会计更正或口径提示
- 数据日期：
- 主要数据来源：
- 本地原始资料：列出本次实际引用的已归档 PDF 相对路径；未成功归档的文件需注明
- 尚未核验的信息：
- 可能影响结论的新公告或市场事件：

## Note-Friendly Block

Append a concise copyable block unless the user explicitly asks not to:

```text
【基本面速记】
公司：
结论：基本面（强/中性/偏弱/高风险），财务质量（优秀/良好/一般/存疑），估值（偏低/合理/偏高/无法判断）。
核心看点：
1.
2.
3.
主要风险：
1.
2.
最新财务预报：近30日预报要点；累计同比；隐含单季同比/环比；信息可信度；盈利质量判断。若无则写近30日未披露。
财务造假风险初筛：低/中/高。理由：
订单/需求验证：改善/稳定/走弱/无法判断。依据：
后续跟踪：

【交易决策摘要】
行情日期：
持仓状态：未持仓/已持仓/未知
当前动作：可以分步买入/小仓试错/等待/持有观察/降仓/退出
建议目标仓位：按项目级默认档位或用户当次参数
参考价格与计划买入区间：
不宜追高位置：
价格止损：按项目级默认止损或用户当次参数计算
基本面提前退出条件：
合理价值/目标空间及依据：
预期盈亏比：
建议有效期：
决策置信度：高/中/低
核心理由：
主要反证：
```
