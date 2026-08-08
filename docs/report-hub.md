# 公开财务报告中心

本仓库通过 GitHub Pages 提供公开的静态报告目录和一个可见但受密码验证保护的持仓入口。**Pages 站点只部署构建脚本生成的 `report-hub-build/` 产物**，该目录已被 Git 忽略且不应手工提交。请注意：若整个 GitHub 仓库已设为公开，仓库中的其他已提交文件和 Git 历史仍可被访问；Pages 的构建隔离不能替代仓库访问控制。

## 已确认的发布策略

- 访问方式：公开网页。
- 发布范围：`reports/<六位代码>/基本面分析/` 中白名单股票的 `*_基本面分析_最新.html`，以及 `hub/portfolio/` 下的**无数据页面壳**。
- 持仓入口：`/portfolio/` 可公开访问锁屏页；验证邮箱密码后才通过 Supabase RLS 请求私有数据。该目录只允许页面代码、Supabase URL 与 publishable key，禁止账户数据、种子、备份、`.env` 与 service-role key。详细配置见 [`portfolio.md`](portfolio.md)。
- 明确排除：时间戳历史版本、草稿、研究轨迹、`reports/_drafts/`、`.research/`、`原始资料/` 及其他报告根目录。
- 白名单和免责声明：`config/publication-policy.json`。
- 基本面报告默认自动加入白名单：`publish_fundamental_review.py` 在 Markdown、HTML、`_最新` 文件和研究轨迹全部成功生成后，按 `publication.auto_include_fundamental_reports` 幂等写入股票代码；脚本拒绝 `reports/_drafts/` 路径和文件名含“草稿”的输入，审查器阻断时不得调用该脚本。
- 源报告不会被修改。构建时仅复制获准 HTML 到 `report-hub-build/reports/<代码>/index.html`，并在**副本**末尾加入报告中心与免责声明链接。

正常使用基本面报告发布脚本即可自动维护白名单；不希望本次报告公开时使用 `--no-publication`。其他报告类型或历史补录仍需先审核，再手工将六位股票代码加入 `allowed_report_codes`；不要放宽文件名或目录规则。

## 本地构建与预览

在仓库根目录运行：

```powershell
python scripts/build_report_hub.py --clean --output report-hub-build
python -m http.server 8000 --directory report-hub-build
```

浏览器打开 <http://localhost:8000>。第二个命令以 `Ctrl+C` 停止。构建校验可单独运行：

```powershell
python scripts/build_report_hub.py --verify-only --output report-hub-build
```

首页支持公司名、股票代码、标题和已公开正文的本地搜索，并可按分类筛选和排序。搜索不依赖后端或第三方服务。

## 首次启用 GitHub Pages

1. 将本实现提交并推送到当前仓库的默认分支。
2. 打开 GitHub 仓库 **Settings → Pages**，在 **Build and deployment / Source** 中选择 **GitHub Actions**。
3. 首次发布可打开 **Actions → Deploy public report hub → Run workflow**，将 `confirm_publication` 选为 `yes` 后运行。
4. 成功后，部署步骤会显示 GitHub Pages URL；通常为 `https://snorlaxy213.github.io/doc-finance/`。

## 自动更新规则

推送到 `main` 时，以下变更会自动重新构建并发布 Pages：

- 白名单股票目录中的 `reports/**/基本面分析/*_基本面分析_最新.html`；
- `config/publication-policy.json`；
- 报告中心模板 `hub/`、构建脚本或本工作流文件。

草稿、时间戳历史版本、研究轨迹、原始资料、`.research/` 及其他目录的变更不会触发发布。每次自动触发仍会执行发布策略校验，因此只有白名单内的最新 HTML 会被复制到公开产物。

仍可在 **Actions → Deploy public report hub → Run workflow** 中手动运行工作流；手动运行时必须将 `confirm_publication` 选为 `yes`。若构建或部署失败，GitHub Pages 会保留上一份成功部署的网站。

## 公开前检查

GitHub Pages 是互联网公开访问。运行工作流前确认白名单内每份最新报告均不含非公开个人信息、账户信息、凭据、受限资料或不应公开的研究内容。站点会展示金融免责声明，但不替代人工审阅。
