# AGENTS.md instructions for C:\Mine\space\doc-finance

<INSTRUCTIONS>

## 项目级个股交易决策默认值

以下规则是所有会输出个股交易动作、仓位或止损的金融 Skills 的唯一默认参数源；各 Skill 引用本节，不得复制一份数值备份。用户在具体任务中明确给出不同参数时，以用户当次参数为准。

- 默认增加“当前位置与交易决策”。
- 默认风控：单股仓位上限为总资金的 25%，价格止损为实际买入均价下方 10%。
- 默认仓位档位：`0% / 12.5% / 25%`。
- 组合计划风险：25% 仓位触发 10% 价格止损时，对总资金的计划损失为 2.5%；跳空、跌停、停牌或流动性不足可使实际损失超过该数值。

## 当前持仓数据源（Supabase）

持仓数据不再维护在本文件，且金融 Skills **不得解析公开持仓 HTML 页面**获取数据。涉及当前持仓、账户资金、仓位、止损、交易动作或观察清单时，先从本机受保护的数据源读取默认精简快照：

```powershell
python scripts/portfolio_cli.py snapshot
```

- 该命令需要本机忽略文件 `.env.portfolio` 中的 Supabase URL、service-role key 和账户邮箱；密钥绝不写入报告、前端、Git 或 Skill 输出。
- 默认输出仅含账户汇总、当前持仓、观察清单与已清仓聚合，适合作为复盘和交易决策的事实基准；需要清仓明细、资金事件、资产快照或审计记录时，再执行 `python scripts/portfolio_cli.py snapshot --details`。
- 若命令未配置、失败或快照过期，必须向用户说明无法核验实时持仓；不得以旧报告、HTML 或臆测数值替代。
- 数据由持仓页手工更新，输出中的 `dataStatus` 和 `asOf` 是判断数据时效性的必要字段。用户提供更近的券商信息时，以用户当次信息为准，并提示其同步更新持仓页。
- 账户全量备份使用 `python scripts/portfolio_cli.py backup`；数据库初始导入使用 `python scripts/portfolio_cli.py seed`。

</INSTRUCTIONS>
