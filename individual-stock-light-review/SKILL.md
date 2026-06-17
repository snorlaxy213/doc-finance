---
name: individual-stock-light-review
description: Guide individual-stock light reviews for equities. Use when the user asks for 个股轻复盘, 持仓股每日复盘, 观察股快速复盘, 个股今日表现复盘, or wants to judge whether a stock's daily price/action/news changes its fundamentals, valuation logic, or investment thesis.
---

# Individual Stock Light Review

## Objective

Use this skill to produce a concise daily light review for one or more stocks. Focus on whether today's information changes the company's fundamentals, valuation logic, or investment thesis.

Do not present the review as personal investment advice, trading instructions, or guaranteed return guidance. Frame conclusions as analytical judgments with assumptions and risks.

## Data Discipline

For current market prices, announcements, financial results, regulatory actions, analyst updates, or news, verify with current sources before making factual claims. Prefer primary or authoritative sources:

- Exchange announcements and company investor relations pages
- Official filings, earnings releases, transcripts, and regulatory notices
- Market data pages for index, sector, price, turnover amount, and turnover rate checks
- Central bank, statistics bureau, and policy authority releases for macro drivers

If current data is unavailable, state the information boundary clearly and separate facts from inference.

## Workflow

### 1. Start With A One-Sentence Conclusion

Classify the stock into one of four states:

- `逻辑不变`: price movement is mainly market/sector noise; fundamentals are not materially changed.
- `需要观察`: signal is not enough to change the thesis, but follow-up data is needed.
- `触发深度复盘`: abnormal move, material disclosure, or conflicting signal requires deeper analysis.
- `逻辑受损`: new information weakens revenue, margin, cash flow, balance sheet, governance, or valuation assumptions.

Include confidence level or key premise when appropriate.

### 2. Check Performance And Relative Strength

Compare the stock against:

- Broad market benchmark relevant to listing venue, such as 沪深300, 创业板指, 恒生指数, 恒生科技, S&P 500, or Nasdaq.
- Sector or industry index when available.
- Key peers or leaders in the same business model.

Focus on:

- Daily price change
- Turnover amount and turnover rate change
- Whether the move is consistent with market and sector behavior
- Whether the stock materially underperformed or outperformed peers

### 3. Attribute The Move

Separate likely drivers into three buckets:

- `市场因素`: rates, FX, liquidity, risk appetite, broad index moves.
- `行业因素`: policy, product prices, demand/supply, regulation, competition, sector rotation.
- `公司因素`: earnings, guidance, orders, buyback, dividend, share reduction, litigation, inquiry letter, governance, management change, public opinion.

Avoid over-explaining ordinary price movement. If no clear driver is found, say so.

### 4. Test Fundamental Impact

Ask whether today's information changes:

- Revenue growth assumptions
- Gross margin, expense ratio, or profit margin assumptions
- Cash flow quality, leverage, or balance sheet risk
- Competitive position or industry structure
- Governance and disclosure credibility
- Valuation assumptions, such as growth durability, discount rate, or risk premium

If the answer is no, mark the movement as short-term market behavior unless other evidence contradicts it.

### 5. Check Capital And Shareholder Signals

Only highlight abnormal or material changes:

- Unusual turnover amount or turnover rate
- Block trades, insider or major shareholder reduction/increase
- Buyback or dividend change
- Margin financing or short interest changes where relevant
- Options activity for US/HK stocks when it materially supports the interpretation

Do not treat a single capital-flow signal as decisive without fundamental evidence.

### 6. Decide Whether To Escalate

Escalate from light review to deep review when any condition appears:

- Single-day price move materially deviates from the sector or benchmark.
- Turnover amount or turnover rate expands sharply with price weakness or failed breakout.
- Earnings, guidance, profit warning, major contract, M&A, buyback, dividend, or financing is released.
- Regulatory inquiry, penalty, litigation, audit issue, or governance event appears.
- Major shareholder reduction, management turnover, or pledge/liquidity risk appears.
- Industry pricing, policy, demand, or competitive structure changes.
- Price action persistently contradicts the prior fundamental thesis.

## Output Template

Use this structure for a concise response:

```text
结论摘要：
一句话判断：逻辑不变 / 需要观察 / 触发深度复盘 / 逻辑受损。
置信度或关键前提：

今日表现：
个股涨跌幅、成交额/换手率、相对大盘/行业/同业表现。

原因拆解：
市场因素：
行业因素：
公司因素：

基本面影响：
收入：
利润率：
现金流/资产负债表：
竞争格局/治理：

资金与筹码：
是否有异常放量、股东行为、回购、减持、做空或期权异动。

后续关注：
列出 1-3 个最关键的下一步数据、公告或事件。

风险提示与信息边界：
说明可能导致判断失效的因素，以及哪些数据仍需核验。
```

For multiple stocks, use a compact table first, then expand only the names requiring observation or deep review.

Always append a note-friendly version at the end of every single-stock light review. Do not wait for the user to request it. If a data point is unavailable, keep the field and write `待核验` instead of omitting the block.

```text
个股涨跌幅：
成交额/换手率：
相对大盘和行业：跑赢 / 跑输 / 基本同步
资金/成交是否异常：
结论标签：
后续关注：
```

## Style

- Use simplified Chinese unless the user requests otherwise.
- Lead with the conclusion, then show the reasoning.
- Keep the review concise: light review should usually fit within 300-600 Chinese characters per stock.
- Use professional, cautious investment-analysis language.
- Do not recommend buy/sell/hold as personalized advice.
