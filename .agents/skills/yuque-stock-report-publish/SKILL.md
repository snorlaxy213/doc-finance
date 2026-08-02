---
name: yuque-stock-report-publish
description: Publish Codex-generated Chinese stock research or fundamental-analysis Markdown reports into Yuque. Use when the user asks to save, upload, sync, paste, publish, archive, or organize a stock report, 基本面分析, 个股复盘, or 财报分析 into Yuque/语雀 as a stock page with a child report page.
---

# Yuque Stock Report Publish

## Overview

Use this skill to move a completed Codex stock-analysis report into Yuque as a reusable knowledge-base entry. The recorded workflow created a parent page named for the company, then created a child page named `基本面`, pasted the Markdown report, and verified the pasted content.

Prefer a Yuque API or connector if one is available and authenticated. If no reliable connector is available, use Computer Use to operate the Yuque desktop app or browser UI.

## Inputs

Collect these before publishing:

- `company_name`: Chinese company short name, such as `杭电股份`.
- `stock_code`: Optional but preferred, such as `603618.SH`.
- `report_markdown`: The full Markdown report text or path to the generated `.md` file.
- `summary_note`: Optional short note to append at the end, often headed `【基本面速记】`.
- `target_space`: The Yuque knowledge base or folder where stock pages are stored, if the user specifies one.

If the company name is ambiguous or the target Yuque space is unknown, inspect the current Yuque window/sidebar first. Ask only if the target cannot be inferred.

## Workflow

1. Prepare the publish text.
   - Read the source Markdown file when a file path is available; do not copy from a rendered UI unless necessary.
   - Preserve headings, tables, links, and source citations.
   - If the report lacks a short note and the user expects one, append a compact `【基本面速记】` section covering conclusion, core positives, key risks, fraud-risk screen, order/demand validation, and follow-up items.
   - Do not include passwords, account identifiers, private personal details, or other sensitive material found in the source.

2. Open Yuque.
   - Use the existing Yuque desktop app window or browser tab when it is already open.
   - Navigate to the requested knowledge base/folder. In the recorded workflow, the target folder button was `个股`.

3. Create or locate the parent stock page.
   - If a page for `company_name` already exists, open it instead of creating a duplicate.
   - Otherwise create a new document/page from the folder menu item labeled `文档`.
   - Set the title to `company_name`, submit it, and wait until the page title changes from `无标题文档` to the company name.

4. Create or locate the report child page.
   - From the parent stock page, create/open a child document.
   - Title it `基本面` unless the user requests a different report type.
   - If a `基本面` page already exists, update it only after confirming that replacement or append behavior is appropriate for the user's request.

5. Paste or insert the report.
   - Focus the Yuque document body text area, not the title field.
   - Insert `report_markdown` as the page body. For UI publishing, put the prepared Markdown on the clipboard and use paste.
   - After paste, wait for Yuque to render the content before validating.

6. Verify.
   - Confirm the Yuque page title is `基本面`.
   - Confirm the first report heading includes the company name and stock code when available.
   - Confirm a representative table or section from the source exists after paste.
   - Confirm the `【基本面速记】` section exists when it was part of the source or requested.
   - If Yuque shows unsaved/syncing state, wait until autosave finishes before reporting completion.

## UI Targets From Recording

Use stable targets rather than coordinates:

- App/window: `语雀` with document title such as `基本面`, `无标题文档`, or the company name.
- Create document: menu item `文档`.
- Parent folder: button or sidebar item `个股` when publishing stock pages.
- Title input: text area with placeholder `请输入标题`.
- Body editor: main Yuque document text area after the title is submitted.

The recorded title correction accidentally started with a similar company name and then edited it. Future runs should type the final company name directly.

## Completion Response

Report the Yuque page structure and what was published, for example: `已发布到语雀：公司页「公司名」-> 子页「基本面」`. Mention if an existing page was updated instead of creating a new one.
