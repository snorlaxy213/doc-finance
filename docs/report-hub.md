# 公开财务报告中心

本仓库通过 GitHub Pages 提供公开的静态报告目录。源研究仓库仍可包含原始资料和工作文件；**公开站点只部署构建脚本生成的 `report-hub-build/` 产物**，该目录已被 Git 忽略且不应手工提交。

## 已确认的发布策略

- 访问方式：公开网页。
- 发布范围：`reports/<六位代码>/基本面分析/` 中白名单股票的 `*_基本面分析_最新.html`。
- 明确排除：时间戳历史版本、草稿、研究轨迹、`reports/_drafts/`、`.research/`、`原始资料/` 及其他报告根目录。
- 白名单和免责声明：`config/publication-policy.json`。
- 源报告不会被修改。构建时仅复制获准 HTML 到 `report-hub-build/reports/<代码>/index.html`，并在**副本**末尾加入报告中心与免责声明链接。

要新增公开标的，先审核报告是否适合公开，再将六位股票代码加入 `allowed_report_codes`；不要放宽文件名或目录规则。

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
3. 打开 **Actions → Deploy public report hub → Run workflow**，将 `confirm_publication` 选为 `yes` 后运行。
4. 成功后，部署步骤会显示 GitHub Pages URL；通常为 `https://snorlaxy213.github.io/doc-finance/`。

此工作流没有 `push` 触发器。每次更新公开目录都必须手动确认并触发，部署前会重新生成并校验隔离产物。若工作流失败，GitHub Pages 会保留上一份成功部署的网站。

## 公开前检查

GitHub Pages 是互联网公开访问。运行工作流前确认白名单内每份最新报告均不含非公开个人信息、账户信息、凭据、受限资料或不应公开的研究内容。站点会展示金融免责声明，但不替代人工审阅。
