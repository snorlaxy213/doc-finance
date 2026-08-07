# Requirements Document

## Introduction

Financial_Report_Hub is a proposal-only feature for making selected existing workspace reports discoverable through a GitHub Pages static website. The proposal preserves report sources and requires workspace-owner confirmation before any publication execution.

## Glossary

- **Financial_Report_Hub**: The proposed static website and its supporting publication workflow.
- **Workspace_Owner**: The person authorized to choose reports, access settings, and publication actions.
- **Reader**: A person who views the published Financial_Report_Hub website.
- **Report**: An existing workspace document intended for Reader access, stored as HTML or Markdown.
- **HTML_Report**: A Report stored in HyperText Markup Language (HTML) format.
- **Markdown_Report**: A Report stored in Markdown format.
- **Report_Root**: A workspace directory designated for discovery: `reports/`, `industry/`, `industry-review/`, or `books/`.
- **Report_Variant**: A timestamped, `最新`, draft, or other version of a Report that shares a report subject.
- **Publication_Proposal**: A reviewable selection, access mode, and deployment plan that awaits Workspace_Owner confirmation.
- **Publication_Policy**: The Workspace_Owner-approved rules that determine which Reports and Report_Variants may be public.
- **Access_Mode**: The selected audience visibility for the site: public repository Pages, private repository Pages where supported by the selected GitHub plan, or no publication.
- **Report_Catalog**: The generated collection of Report metadata and website links.
- **Catalog_Metadata**: The title, source path, Report_Root, document format, version label, report date when identifiable, and publication eligibility for a Report.
- **Catalog_Generator**: The proposed workflow component that creates the Report_Catalog from eligible existing Reports.
- **Search_Interface**: The website capability that matches catalog entries against reader-entered query text.
- **Filter**: A reader-selected Report_Catalog constraint based on Report_Root, document format, report date, or version label.
- **Navigation_Interface**: Website links and hierarchy that lead readers among the home page, Report_Root collections, search results, and individual Reports.
- **GitHub_Pages_Deployment**: A static-site publication operation provided by GitHub Pages.
- **Publication_Execution**: Any action that copies, transforms, commits, uploads, or deploys Reports for website access.
- **Financial_Disclaimer**: A visible statement that Reports are informational research and do not constitute investment advice or a solicitation.
- **Sensitive_Data**: non-public personal, account, credential, proprietary, or restricted source information.
- **Accessible_Mobile_Experience**: Website behavior that is usable by keyboard and assistive technology and readable on small-screen devices.

## Requirements

### Requirement 1: Reviewable publication proposal

**User Story:** As a Workspace_Owner, I want to review the intended audience, access options, selected reports, and consequences before publication, so that I retain control of financial-research distribution.

#### Acceptance Criteria

1. WHEN the Workspace_Owner requests a publication proposal, THE Financial_Report_Hub SHALL present the intended audience, each Access_Mode, and the access implications of each Access_Mode.
2. WHEN the Workspace_Owner requests a publication proposal, THE Financial_Report_Hub SHALL identify the eligible Report_Roots and the Report_Variants proposed for publication.
3. WHILE a Publication_Proposal lacks Workspace_Owner confirmation, THE Financial_Report_Hub SHALL retain the proposal in a non-executing state.
4. IF the Workspace_Owner rejects a Publication_Proposal or confirms no publication, THEN THE Financial_Report_Hub SHALL record no Publication_Execution for the proposal.
5. WHEN the Workspace_Owner confirms a Publication_Proposal, THE Financial_Report_Hub SHALL record the confirmed Access_Mode and Publication_Policy before Publication_Execution.

### Requirement 2: Discover and preserve existing reports

**User Story:** As a Workspace_Owner, I want existing reports discovered without changing source materials, so that historical research remains intact.

#### Acceptance Criteria

1. WHEN the Catalog_Generator examines a Report_Root, THE Catalog_Generator SHALL identify HTML_Reports and Markdown_Reports without modifying the source files.
2. WHEN the Catalog_Generator identifies a Report, THE Catalog_Generator SHALL capture Catalog_Metadata from the Report path, filename, and document format.
3. WHEN the Catalog_Generator identifies Report_Variants for one report subject, THE Catalog_Generator SHALL distinguish timestamped variants, `最新` variants, and draft variants in Catalog_Metadata.
4. IF a Report lacks an HTML_Report, THEN THE Catalog_Generator SHALL mark the Report as requiring a presentation decision in the Publication_Proposal.
5. WHILE a Report is excluded by the Publication_Policy, THE Catalog_Generator SHALL omit the Report from the public Report_Catalog.


### Requirement 3: Generate a publication catalog

**User Story:** As a Reader, I want a current index of eligible reports, so that I can identify available financial research without browsing source directories.

#### Acceptance Criteria

1. WHEN the Workspace_Owner initiates a confirmed catalog update, THE Catalog_Generator SHALL attempt to generate one Report_Catalog entry for each Report eligible under the Publication_Policy.
2. WHEN the Catalog_Generator generates a Report_Catalog entry, THE Catalog_Generator SHALL include the Catalog_Metadata and a link to the selected reader-facing Report representation.
3. WHEN the Catalog_Generator processes Report_Variants for a report subject, THE Catalog_Generator SHALL expose the selected current variant and retain separately selected historical variants as distinct catalog entries.
4. IF the Catalog_Generator cannot generate a Report_Catalog entry for an eligible Report, THEN THE Catalog_Generator SHALL identify the Report and the reason in the update result.
5. WHEN the Catalog_Generator cannot generate a Report_Catalog entry for an eligible Report, THE Catalog_Generator SHALL continue generating entries for other eligible Reports.
6. WHEN a confirmed catalog update completes, THE Financial_Report_Hub SHALL provide a Navigation_Interface entry point to the generated Report_Catalog.

### Requirement 4: Find reports through navigation, search, and filters

**User Story:** As a Reader, I want to browse and narrow the report collection, so that I can reach relevant research efficiently.

#### Acceptance Criteria

1. THE Navigation_Interface SHALL display links to the home page and each Report_Root collection on every reader-facing page.
2. WHEN a Reader opens a Report_Root collection, THE Navigation_Interface SHALL present the eligible Report_Catalog entries for that Report_Root.
3. WHEN a Reader submits query text, THE Search_Interface SHALL return Report_Catalog entries whose title or source path contains the query text.
4. WHEN a Reader applies a Filter, THE Search_Interface SHALL display only Report_Catalog entries that satisfy the selected Filter.
5. WHEN a Reader opens a Report_Catalog entry, THE Navigation_Interface SHALL provide a link to the selected reader-facing Report representation.
6. IF a search or Filter produces zero matches, THEN THE Search_Interface SHALL display a zero-results state and preserve the Reader query and selected Filters.

### Requirement 5: Provide mobile and accessible reading

**User Story:** As a Reader using a phone, keyboard, or assistive technology, I want the report hub to remain navigable and readable, so that I can access research without device or input barriers.

#### Acceptance Criteria

1. THE Accessible_Mobile_Experience SHALL present the home page, Report_Catalog, Search_Interface, and Navigation_Interface without horizontal page scrolling at a viewport width of 320 CSS pixels.
2. WHEN a Reader navigates interactive controls by keyboard, THE Accessible_Mobile_Experience SHALL provide a visible keyboard focus indicator and a keyboard-operable action for each control.
3. WHEN the Search_Interface displays results, THE Accessible_Mobile_Experience SHALL provide programmatically associated labels for the query control and each Filter control.
4. WHEN a Report_Catalog entry links to an HTML_Report, THE Accessible_Mobile_Experience SHALL provide the Report title as the accessible link name.

### Requirement 6: Protect data and disclose financial limitations

**User Story:** As a Workspace_Owner, I want publication controls and clear financial disclosures, so that public research sharing does not expose restricted material or misrepresent financial content.

#### Acceptance Criteria

1. WHEN the Workspace_Owner reviews a Publication_Proposal, THE Financial_Report_Hub SHALL identify Reports that require Sensitive_Data review before inclusion in the Publication_Policy.
2. WHILE a Report is marked as requiring Sensitive_Data review, THE Financial_Report_Hub SHALL exclude the Report from Publication_Execution.
3. WHEN the Workspace_Owner records an inclusion decision in the confirmed Publication_Policy for a Report requiring Sensitive_Data review, THE Financial_Report_Hub SHALL mark the Report eligible for Publication_Execution.
4. WHEN the Financial_Report_Hub presents a reader-facing Report, THE Financial_Report_Hub SHALL display a Financial_Disclaimer on the report page or through a clearly labeled link available from the report page.
5. WHEN the Financial_Report_Hub presents the home page, THE Financial_Report_Hub SHALL provide a clearly labeled link to the Financial_Disclaimer.
6. IF a Publication_Proposal includes a Report that is not eligible under the confirmed Publication_Policy, THEN THE Financial_Report_Hub SHALL identify the Report as excluded before Publication_Execution.

### Requirement 7: Publish and update with GitHub Pages

**User Story:** As a Workspace_Owner, I want a confirmed, repeatable GitHub Pages update workflow, so that the published catalog and selected reports remain current.

#### Acceptance Criteria

1. WHEN the Workspace_Owner confirms a Publication_Proposal with an enabled Access_Mode, THE Financial_Report_Hub SHALL define the GitHub_Pages_Deployment source, the selected Report representations, and the confirmed Publication_Policy in the publication record.
2. WHEN the Workspace_Owner initiates a confirmed publication update, THE Financial_Report_Hub SHALL regenerate the Report_Catalog before the GitHub_Pages_Deployment.
3. WHEN a GitHub_Pages_Deployment succeeds, THE Financial_Report_Hub SHALL report the published website address and the update outcome to the Workspace_Owner.
4. IF a GitHub_Pages_Deployment fails, THEN THE Financial_Report_Hub SHALL report the failed deployment outcome and retain the previous published site contents.
5. WHILE the Access_Mode is no publication, THE Financial_Report_Hub SHALL prevent new GitHub_Pages_Deployment attempts.
6. WHEN an Access_Mode changes to no publication during a GitHub_Pages_Deployment, THE Financial_Report_Hub SHALL allow the in-progress GitHub_Pages_Deployment to complete.
7. WHEN the Workspace_Owner changes the Publication_Policy, THE Financial_Report_Hub SHALL require Workspace_Owner confirmation before the next GitHub_Pages_Deployment.

## Open Decisions for Workspace_Owner Confirmation

- Select the intended Reader audience and Access_Mode.
- Select the Report_Roots, Report_Variants, and presentation decision for Markdown_Reports without HTML_Reports.
- Approve the Publication_Policy, including Sensitive_Data review decisions and the Financial_Disclaimer wording.
- Confirm whether historical timestamped variants, `最新` variants, and research-trace Reports should be reader-visible.
- Confirm the GitHub repository and GitHub Pages source before any Publication_Execution.
