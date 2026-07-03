---
name: stock-selection-analysis
description: Chinese stock-selection and earnings-growth due-diligence analysis with a fixed output template. Use when Codex needs to analyze whether a stock/company with strong profit growth is worth tracking, interpret prosperity or demand clues in announcements, validate financial quality, sustainability, valuation, and risks, or answer Chinese requests such as 选股分析, 业绩大增能买吗, 景气线索怎么解读, 股票购买决策框架, or 固定股票分析模板.
---

# Stock Selection Analysis

## Core Rules

Use Chinese by default. Treat the work as an investment research framework, not personalized financial advice. Do not give absolute commands such as "must buy", "all in", or "guaranteed". Use research conclusions such as `回避`, `观察`, `小仓试错`, or `重点买入候选`.

For a real company or stock, use current, dated sources before forming a conclusion. Prefer official filings, exchange announcements, company investor-relations materials, audited/interim/quarterly reports, and regulator or exchange education materials. For A-share companies, prefer company公告, 交易所公告, 定期报告, 巨潮资讯/交易所披露, then reputable financial data providers. For US-listed companies, prefer SEC filings and company IR. For Hong Kong-listed companies, prefer HKEX filings and company IR.

Always state the analysis date and data period. If current data is unavailable, say so clearly and mark affected fields as `待核验`. Do not invent exact financial numbers, valuation percentiles, order data, capacity utilization, or peer comparisons.

Every output must keep the fixed template below. Do not omit sections. If evidence is missing, write `未披露/待核验` and explain what would verify it.

When analyzing a listed stock, include a trend-template check for whether the stock is in stage 2 uptrend. The trend check is a technical filter, not a buy signal, and it must not replace the fundamental, prosperity, valuation, and risk gates. Mark any unavailable market, moving-average, 52-week, or relative-strength field as `待核验`; do not infer it.

## Analysis Logic

Analyze a performance-growth company through five gates:

1. `增长是不是真的`: verify revenue, attributable net profit, non-GAAP/deducted non-recurring profit where applicable, operating cash flow, gross margin, net margin, receivables, inventory, and non-recurring gains.
2. `增长来自哪里`: identify whether growth comes from industry prosperity, market-share gain, new products, price increases, cost decline, consolidation, asset disposal, subsidies, FX gains, or accounting treatment.
3. `还能持续多久`: translate prosperity language into verifiable indicators, then test orders, capacity, competitors, downstream demand, price cycle, inventory, and cash conversion.
4. `估值是否已经透支`: compare current valuation with history, peers, expected 1-2 year profit growth, market cap/profit space, and recent share-price gains.
5. `有没有硬伤`: check pledge, shareholder/executive selling, goodwill, abnormal receivables/inventory, audit opinion, related-party transactions, cash-flow weakness, project delays, leverage, and regulatory issues.

Use this formula as the decision lens:

`能买 = 业绩真实 + 景气可持续 + 公司有优势 + 估值没透支 + 风险可控`

The formula is not an automatic buy signal. It is a disciplined way to decide the research tier.

Use this trend formula as an additional technical lens:

`趋势合格 = 价格站上150日/200日均线 + 150日均线高于200日均线 + 200日均线至少上行1个月 + 50日均线高于150日/200日均线 + 股价较52周低点至少上涨25% + 股价处于52周高点25%以内 + RS排名不低于70且RS线至少上涨6周 + 股价站上50日均线`

Only when all eight trend conditions pass can the output say `符合上涨趋势第二阶段`. If fundamental evidence is strong but the trend template fails or is incomplete, classify the stock as fundamental follow-up or observation rather than treating it as technically confirmed.

## Prosperity Clue Translation

When a company uses promotional language, translate it into measurable indicators:

| 公司说法 | 真正含义 | 必须验证 |
|---|---|---|
| 产品供不应求 | 需求大于产能 | 合同负债、在手订单、产能利用率、交付周期、客户预付款是否上升 |
| 行业高景气度上行 | 整个行业需求变好 | 同行业公司收入/利润、行业价格、销量、库存、开工率是否同步向上 |
| 市场超预期拓展 | 新客户、新区域、新渠道打开 | 新客户收入占比、海外/区域收入、销售费用、客户集中度、渠道库存 |
| 新品上市持续超预期 | 新产品开始放量 | 新品收入占比、订单、毛利率、是否替代老产品、研发/产能匹配 |
| 产品价格中枢持续上涨 | 有涨价能力或供需紧张 | 毛利率是否提升，涨价是否被原材料/费用吞掉，价格是否可持续 |
| 供给偏紧 | 行业产能不足 | 行业扩产周期、竞争对手扩产、库存水平、进口/替代供给 |
| 需求旺盛 | 下游真实购买强 | 收入、订单、合同负债、经营现金流、回款是否同步增强 |

Distinguish:

- `真景气`: 收入增长、毛利率提升、现金流变好、合同负债增加、存货周转正常、同行也验证。
- `假景气或尾部景气`: 公司说需求旺盛，但应收账款暴增、存货暴增、现金流弱，或行业集中扩产、渠道压货、价格已经见顶。

## Fixed Output Template

Use this structure exactly, with all headings preserved.

```markdown
# [公司名称/股票代码] 选股分析（截至 [YYYY-MM-DD]）

> 说明：这是研究框架，不构成个性化买卖建议。  
> 数据口径：[年报/季报/业绩预告/公告/行情数据的日期与范围]  
> 核心问题：业绩大增之后，是否具备进入买入候选池的条件？

## 1. 一句话结论

- 研究档位：[回避 / 观察 / 小仓试错 / 重点买入候选]
- 趋势模板状态：[符合上涨趋势第二阶段 / 部分符合，仍需观察 / 不符合 / 待核验]
- 核心判断：[用 2-3 句话说明为什么]
- 最强证据：[列出 1-3 条]
- 最大不确定性：[列出 1-3 条]
- 下一步验证点：[列出下一份财报、订单、价格、现金流、估值或风险验证点]

## 2. 五道门快速评分

| 维度 | 评分 | 结论 | 关键证据/待核验 |
|---|---:|---|---|
| 业绩真实性 | [0-2] | [强/中/弱] | [证据或待核验] |
| 增长来源质量 | [0-2] | [强/中/弱] | [证据或待核验] |
| 景气持续性 | [0-2] | [强/中/弱] | [证据或待核验] |
| 竞争优势 | [0-2] | [强/中/弱] | [证据或待核验] |
| 估值未透支 | [0-2] | [强/中/弱] | [证据或待核验] |
| 风险可控 | [0-2] | [强/中/弱] | [证据或待核验] |

- 总分：[0-12]
- 分档规则：0-4 回避；5-7 观察；8-9 小仓试错；10-12 重点买入候选。
- 注意：评分只是研究分层，不是自动买入信号。

## 3. 第一道门：增长是不是真的

| 核验项 | 看到什么 | 判断 | 证据 |
|---|---|---|---|
| 营收 | [同比/环比/规模] | [同步增长/背离/待核验] | [来源] |
| 归母净利润 | [同比/环比/规模] | [增长质量] | [来源] |
| 扣非净利润 | [同比/环比/规模] | [是否跟上] | [来源] |
| 经营现金流 | [金额/同比/与利润关系] | [是否跟上] | [来源] |
| 毛利率/净利率 | [变化] | [改善/恶化/待核验] | [来源] |
| 应收账款 | [变化] | [是否异常] | [来源] |
| 存货 | [变化] | [是否异常] | [来源] |
| 非经常性损益 | [金额/占比] | [是否撑利润] | [来源] |

小结：[利润增长是否被收入、现金流、盈利能力共同验证。]

## 4. 第二道门：增长来自哪里

| 增长来源 | 判断 | 证据 | 质量评价 |
|---|---|---|---|
| 行业景气 | [是/否/待核验] | [证据] | [高/中/低] |
| 市占率提升 | [是/否/待核验] | [证据] | [高/中/低] |
| 新品放量 | [是/否/待核验] | [证据] | [高/中/低] |
| 涨价 | [是/否/待核验] | [证据] | [高/中/低] |
| 成本下降 | [是/否/待核验] | [证据] | [高/中/低] |
| 并表/一次性因素 | [是/否/待核验] | [证据] | [高/中/低] |

主要驱动：[用一句话归纳主因。]  
质量判断：[最好是收入增长 + 毛利率提升 + 现金流改善 + 市占率提升；最差是非经常性收益或会计处理。]

## 5. 第三道门：景气还能持续多久（重点）

### 5.1 公司说法翻译

| 公司说法/公告表述 | 真正含义 | 可验证指标 | 当前证据 | 结论 |
|---|---|---|---|---|
| [例如需求旺盛/供不应求/价格上涨] | [翻译成经济含义] | [订单、合同负债、产能、价格、现金流等] | [证据或待核验] | [已验证/未验证/反证] |

### 5.2 持续性核验

| 问题 | 结论 | 证据/待核验 |
|---|---|---|
| 订单能看到几个季度？ | [结论] | [证据] |
| 产能是否满产？ | [结论] | [证据] |
| 新增产能什么时候释放？ | [结论] | [证据] |
| 竞争对手是否也在扩产？ | [结论] | [证据] |
| 下游需求是短期补库存还是长期渗透率提升？ | [结论] | [证据] |
| 涨价是供需紧张还是成本被动传导？ | [结论] | [证据] |
| 现金流和回款是否支持真实需求？ | [结论] | [证据] |

景气判断：[真景气 / 假景气 / 尾部景气 / 暂无法判断]  
一句话解释：[说明为什么。]

## 6. 第四道门：估值是否已经透支

| 估值项 | 当前情况 | 对比口径 | 判断 |
|---|---|---|---|
| PE | [数值/待核验] | [历史分位/同行] | [便宜/合理/偏贵/待核验] |
| PB | [数值/待核验] | [历史分位/同行] | [便宜/合理/偏贵/待核验] |
| PS | [数值/待核验] | [历史分位/同行] | [便宜/合理/偏贵/待核验] |
| 未来 1-2 年利润增速 | [预测/待核验] | [一致预期/公司指引/自行估算] | [匹配/不匹配/待核验] |
| 近 6-12 个月股价涨幅 | [涨幅/待核验] | [利润增速/行业涨幅] | [是否提前反映] |

估值小结：[好公司也可能买贵；说明当前价格是否已经反映大部分好消息。]


## 6.5 趋势模板检查：是否处于上涨趋势第二阶段

> 说明：该部分仅用于技术面趋势过滤，不构成买卖建议。若 RS 排名无法取得，应标记为“待核验”，或说明采用的替代口径。

| 标准 | 判定 | 当前数据 | 说明 |
|---|---|---|---|
| 股价高于150日和200日均线 | [通过/不通过/待核验] | [当前价、MA150、MA200] | [说明] |
| 150日均线高于200日均线 | [通过/不通过/待核验] | [MA150、MA200] | [说明] |
| 200日均线上涨至少1个月 | [通过/不通过/待核验] | [近1个月MA200变化] | [最好观察4-5个月以上] |
| 50日均线高于150日和200日均线 | [通过/不通过/待核验] | [MA50、MA150、MA200] | [说明] |
| 股价较52周低点至少高25% | [通过/不通过/待核验] | [当前价、52周低点、涨幅] | [说明] |
| 股价处于52周高点25%以内 | [通过/不通过/待核验] | [当前价、52周高点、回撤幅度] | [越接近新高越强] |
| RS排名不低于70，且RS线至少上涨6周 | [通过/不通过/待核验] | [RS排名/RS线趋势/替代RS口径] | [更优状态通常接近90，RS线最好上涨13周以上] |
| 当前股价在50日均线之上 | [通过/不通过/待核验] | [当前价、MA50] | [说明] |

趋势结论：[符合上涨趋势第二阶段 / 部分符合，仍需观察 / 不符合 / 数据不足无法判断]  
关键短板：[列出未通过或待核验项目]  
与研究档位的关系：[若趋势不符合，即使基本面较强，也应说明是否仅作基本面跟踪；若趋势符合但基本面证据不足，不能单独上调档位。]
## 7. 第五道门：硬伤与风险

| 风险项 | 是否存在 | 证据 | 处理 |
|---|---|---|---|
| 大股东高比例质押 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |
| 高管或大股东减持 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |
| 商誉较大 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |
| 应收账款异常增长 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |
| 存货异常增长 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |
| 审计意见异常 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |
| 关联交易复杂 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |
| 现金流长期弱于利润 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |
| 募投项目延期或不达预期 | [是/否/待核验] | [来源] | [一票否决/降权/跟踪] |

风险小结：[说明最大风险和是否影响研究档位。]

## 8. 操作分档与验证计划

| 档位 | 适用条件 | 对本公司的判断 |
|---|---|---|
| 回避 | 财务质量差、估值严重透支、硬伤明显或景气反转 | [是否适用] |
| 观察 | 业绩好，但现金流/估值/持续性仍不确定 | [是否适用] |
| 小仓试错 | 财务验证较好，但股价偏高或持续性还需确认 | [是否适用] |
| 重点买入候选 | 业绩、现金流、毛利率、订单、估值和风险都匹配 | [是否适用] |

验证计划：
- 未来 1 个季度必须验证：[指标]
- 未来 2-4 个季度必须验证：[指标]
- 趋势跟踪项：[50日/150日/200日均线、52周高低点、RS排名或替代RS线、股价是否持续在50日均线上方]
- 失效条件：[哪些情况出现后应下调档位]
- 加分条件：[哪些情况出现后可上调档位]

## 9. 资料来源

- [来源名称]：[日期]，[链接或说明]
- [来源名称]：[日期]，[链接或说明]

## 10. 最终一句话

[第三点是景气暗号，不是买入按钮。真正值得进入买入候选池的，是景气正在上行、财务已经验证、估值没有明显透支、未来几个季度仍能兑现的公司。结合本公司证据，给出一句最终判断。]
```

## Scoring Guidance

Use 0, 1, or 2 for each scoring row:

- `2`: strong evidence and no major contradiction.
- `1`: partial evidence, mixed signals, or material data still pending.
- `0`: evidence is weak, contradicted, missing for a critical item, or shows clear risk.

If any one-vote veto risk is severe, cap the final research tier at `观察` or `回避` even when the total score is high.

## Response Discipline

When data is incomplete, be explicit: "目前不能判断是否可买，只能判断是否值得继续研究." Avoid false precision. Keep the conclusion tied to evidence.

When the user asks only for "第三点怎么解读", still use the prosperity translation and sustainability sections, then add a shorter conclusion. When the user asks for a full stock analysis, use the complete fixed template.
