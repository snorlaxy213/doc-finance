# AGENTS.md instructions for C:\Mine\space\doc-finance

<INSTRUCTIONS>

## 项目级个股交易决策默认值

以下规则是所有会输出个股交易动作、仓位或止损的金融 Skills 的唯一默认参数源；各 Skill 引用本节，不得复制一份数值备份。用户在具体任务中明确给出不同参数时，以用户当次参数为准。

- 基本面报告默认增加“当前投资价值与介入条件”，观察未来 12—24 个月，不强制输出技术走势、交易动作、个人仓位或成本止损。仅当用户明确要求交易计划时增加交易决策，并使用以下风控参数；其他金融 Skills 按各自范围输出。
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

## Git 工作流

- 当前项目不使用 `git-commit` Skill 或其提交规范；提交与推送无需执行该 Skill 的分支、提交信息或确认检查。

## 基本面报告公开发布

- 每次完成一份正式的个股基本面报告后，默认将其六位股票代码加入 `config/publication-policy.json` 的 `allowed_report_codes`，使 `reports/<代码>/基本面分析/*_基本面分析_最新.html` 能进入 GitHub Pages 公开目录。
- 报告应通过 `publish_fundamental_review.py` 发布，并显式指定本仓库的 `reports` 目录及 `config/publication-policy.json`；除非用户明确要求本次不公开，否则不得使用 `--no-publication`。
- 提交前检查白名单已包含该代码、最新 HTML 文件已生成，并确认 Git 提交同时包含报告文件和白名单配置变更。
- 使用 `fundamental-stock-review` Skill 生成正式报告并完成发布前检查后，默认先执行 `git commit`，提交成功后再执行 `git push`，将本次报告、白名单配置及相关归档同步到当前远程分支；若用户明确要求不提交或不推送，则按用户要求执行。
- 草稿、`reports/_drafts/`、研究轨迹、历史版本和原始资料不得加入公开目录。

</INSTRUCTIONS>
