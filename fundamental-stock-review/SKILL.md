---
name: fundamental-stock-review
description: Analyze a listed company's fundamentals with a fixed structure covering business quality, industry position, orders/backlog, contract wins, growth, profitability, cash-flow quality, balance-sheet quality, valuation, ownership, institutional participation, market share, losses, negative news, and financial-fraud risk flags. Use when the user asks for 基本面分析, 财报分析, 财务质量分析, 股票深度复盘, 订单跟踪, 中标分析, 重大合同, 订单消息整理, backlog, 合同负债, 客户采购, 招投标信息, 是否财务造假, or wants to evaluate a stock using indicators such as 流通市值, 市盈率, 净利润, 同比增长, 每股收益, ROE, 毛利率, 十大股东占比, 机构家数, 市场占有率, 亏损, or 负面新闻.
---

# Fundamental Stock Review

## Core Rules

- Answer in Simplified Chinese unless the user asks otherwise.
- Use a professional investment-research tone. Do not provide personalized buy/sell instructions or guaranteed-return language.
- Verify current, time-sensitive facts before concluding: ticker/name mapping, latest filings, latest price/market-cap data, major announcements, regulatory actions, and recent negative news.
- Separate confirmed disclosure from market rumor or narrative. Label uncertain items as 信息边界.
- For orders, contracts, and bidding information, distinguish 招标, 中标候选人, 中标公告, 合同签署, 框架协议, delivered revenue, and unverified market rumor.
- Treat negative governance, audit, regulatory, or cash-flow issues as possible conclusion downgrades even when growth and valuation look attractive.
- Do not infer financial fraud from a single indicator. Present it as fraud-risk screening unless there is confirmed regulatory, audit, or legal evidence.

## Data Collection Checklist

Collect the latest available data from public filings, exchange announcements, financial data providers, and credible news sources:

- Current valuation snapshot: latest price date, closing price, total market cap, free-float market cap, PE, PB, PS, dividend yield if relevant. Treat these as latest point-in-time market data, not historical financial-statement metrics.
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

1. Put key data first: start the output with the latest valuation snapshot, then separate current-year interim financial metrics from recent annual financial metrics, with concise change interpretation before long narrative analysis.
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

### 1. 核心财务指标

Do not mix interim reports and annual reports in one core financial table. Use three blocks in this order: latest valuation snapshot, disclosed current-year interim reports, and recent three-year annual reports. Use `亿元` for money amounts, `元/股` for EPS, and `%` for ratios unless otherwise stated. Use `未披露` or `不适用` when data cannot be confirmed.

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

#### 1.2 已披露当年期间财报

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

#### 1.3 最近三年年度财报

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

- 基本面判断：强 / 中性 / 偏弱 / 高风险
- 财务质量：优秀 / 良好 / 一般 / 存疑
- 估值状态：偏低 / 合理 / 偏高 / 无法判断
- 财务造假风险初筛：低 / 中 / 高
- 核心理由：用 3-5 条说明，不超过一屏

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

- 新增订单金额：
- 年初至今累计订单金额：
- 订单金额/上年营收：
- 重点客户复购与新增客户：
- 中标候选人转正式中标/签约情况：
- 合同负债、存货、应收账款和经营现金流变化：
- 触发深度复盘条件：

### 12. 信息边界

- 数据日期：
- 主要数据来源：
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
财务造假风险初筛：低/中/高。理由：
订单/需求验证：改善/稳定/走弱/无法判断。依据：
后续跟踪：
```
