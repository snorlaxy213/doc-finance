# 持仓复盘模块

## 设计边界

- `hub/portfolio/` 是公开报告中心中可见的静态入口；它只包含页面代码和 Supabase **publishable key** 配置，不包含账户、持仓、备份或 `service_role` 密钥。
- 数据保存在 Supabase PostgreSQL，全部业务表按 `owner_id = auth.uid()` 启用 RLS。首次验证邮箱+密码后，页面才读取数据；每次打开、刷新或重新进入持仓页都会要求密码。
- 研究报告继续保存于 `reports/` 并由既有构建流程发布；持仓页仅以证券代码链接到报告，不复制正文到数据库。
- 当前行情、现金和资产快照均由用户手工维护。没有自动行情、自动交易、完整交易流水或公司行为模块。

## 首次配置

1. 在 [Supabase](https://supabase.com/) 创建一个 Free 项目。Free 档足够个人使用，但项目连续一周无访问会暂停，且没有自动备份。
2. 在 **Authentication → Providers** 启用 Email/Password。通过 Authentication 用户面板创建一个仅供自己使用的邮箱密码用户；如启用了邮箱确认，请先完成确认。
3. 在 SQL Editor 执行 [`../supabase/portfolio_schema.sql`](../supabase/portfolio_schema.sql)。该文件创建表、RLS、审计触发器、卖出/清仓/更正/恢复 RPC 与备份恢复 RPC。
4. 将 `.env.portfolio.example` 复制为 `.env.portfolio` 并填写本机配置：

   ```powershell
   Copy-Item .env.portfolio.example .env.portfolio
   ```

   `PORTFOLIO_SUPABASE_SERVICE_ROLE_KEY` 仅允许出现在本机 `.env.portfolio`。它被 `.gitignore` 排除，绝不能放入 `hub/`、GitHub Pages、报告或聊天输出。
5. 在 [`../hub/portfolio/portfolio-config.js`](../hub/portfolio/portfolio-config.js) 中填写项目 URL 和 **publishable key**。该文件会被复制到公开静态页面；publishable key 可公开，数据安全依赖邮箱密码和 RLS。不要填写 service-role key。
6. 使用批准的私有基线初始化数据：

   ```powershell
   python scripts/portfolio_cli.py seed
   ```

   默认输入 `config/portfolio-seed.local.json`，该文件已经被 `.gitignore` 排除。若需要创建其他账户，复制 `config/portfolio-seed.example.json` 为新的本地文件并以 `--file` 指定。
7. 本地预览：

   ```powershell
   python scripts/build_report_hub.py --clean --output report-hub-build
   python -m http.server 8000 --directory report-hub-build
   ```

   打开 `http://localhost:8000/portfolio/`。部署 GitHub Pages 时，同一入口会在 `<Pages URL>/portfolio/` 可见。

## 页面操作口径

- **新增/编辑持仓**：保存当前数量、成本、现价、目标仓位、止损、建仓逻辑和计划。全局默认风控仍以 `AGENTS.md` 为唯一来源；数据库只存具体执行值。
- **部分卖出**：填写数量、成交价和费用。系统累加该持仓的已实现盈亏、卖出金额和费用，剩余仓位继续按成本价计算浮盈。
- **完全清仓**：卖出数量等于当前持仓时，系统将此前累计已实现盈亏与最后一笔卖出汇总为一条清仓记录，并删除当前持仓。
- **更正 / 恢复**：已清仓记录必须填写原因后才能更正；恢复会撤回清仓记录并生成可编辑当前持仓。审计日志记录变更摘要，不是完整交易流水。
- **账户收益**：`调整收益 = 最新总资产 - 初始净资产 - 系统启用后净入金`。只在记录了资产快照和资金事件时有解释价值；页面会始终标注数据更新时间。
- **观察清单**：只保存计划买入区间、失效条件、复盘日期与报告链接；转为持仓后会删除观察清单项。

## 备份与 Skill 数据接口

- 页面“导出完整备份”会下载 JSON；导入恢复会覆盖当前用户的账户、持仓、清仓、观察、资金事件和资产快照。恢复前应先导出一份当前备份。
- 本机命令行完整备份：

  ```powershell
  python scripts/portfolio_cli.py backup
  ```

  默认写入被 Git 忽略的 `portfolio-backups/`。
- 所有金融 Skill 读取默认快照：

  ```powershell
  python scripts/portfolio_cli.py snapshot
  ```

  需要清仓明细、资金事件、资产快照或审计日志时才使用：

  ```powershell
  python scripts/portfolio_cli.py snapshot --details
  ```

  `snapshot` 输出中的 `dataStatus` 和 `asOf` 是数据时效性的必要字段。配置缺失、命令失败或快照过期时，Skill 必须说明无法核验实时持仓，不得改从 HTML 或旧报告推断。

## 发布前安全检查

- 确认 `hub/portfolio/portfolio-config.js` 只含 URL 与 publishable key；禁止任何 service-role key、账户数据、备份或种子 JSON。
- `config/portfolio-seed.local.json`、`.env.portfolio` 和 `portfolio-backups/` 必须保持忽略状态。
- GitHub Pages 只公开页面壳。登录页本身可见，但没有密码无法通过 RLS 读取账户数据。
- Supabase Free 无自动备份。重要清仓、批量更新和数据恢复前后都应导出 JSON 备份。
