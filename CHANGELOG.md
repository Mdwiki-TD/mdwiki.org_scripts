-   Develop flask web application providing batch maintenance tools for mdwiki.org. [#1](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/1) [#2](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/2) [#3](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/3)

-   Adds a pytest suite covering the jobs runtime, auth surface, every blueprint, and per-service pure logic. [#4](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/4)

-   Added background job system for long-running operations with real-time progress tracking and live updates. [#5](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/5)

-   OAuth-based access control; new API utilities for page edits, moves, and text/category retrieval; Commons client helpers and mwclient wrappers added. [#6](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/6)

-   Launched six new job types: Create Redirects, Duplicate Redirect, Find & Replace, Fix Redirects in All Pages, Normalize References, and Import Page History. [#7](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/7)

-   More robust handling of missing/empty API responses and improved capture/reporting of edit/save outcomes. [#8](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/8)
-   Updated wiki domain configuration to handle missing language and family settings more gracefully, with improved fallback behavior when configuration is incomplete. [#9](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/9)
-   Add job placeholders and reorganize tools UI. [#10](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/10)

-   Full "Add R column" job implemented end-to-end; client-side autocomplete, card tools, and dark-mode support added. [#16](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/16)
-   Improved network request error handling with specific handling for timeouts, HTTP errors, and JSON decode failures. [#17](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/17)
-   More reliable save operations with clearer failure logging and result handling. [#18](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/18)
-   Improved job lifecycle management with standardized worker architecture. [#19](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/19)

-   Simplified cancellation detection and ensured cancellation state is reflected in running jobs. [#20](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/20)
-   Fix job status and cancellation updates in result files. [#22](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/22)
-   Added a dedicated database error page to show a friendly "Database Error!" message when the app cannot initialize the database. [#23](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/23)
-   Added user profile dashboard displaying job statistics and a table of recent jobs with timestamps and quick-view links. [#24](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/24)
-   Login/start button styling standardized to outline variants. CSRF rendering unified across job forms. "Details" links simplified and job listing UI streamlined. [#25](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/25)
-   introduces an admin dashboard and coordinator management functionality. [#26](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/26)
-   Job detail pages now show summary stats as Bootstrap cards and split processed pages into separate cards (changed/fixed vs remaining) with diff links. [#27](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/27)
-   refactors and consolidates the job workers by introducing a shared <code>SharedworkerObject</code> and <code>UpdaterOutcome</code> structure, removing duplicate code across several workers, and updating the corresponding HTML templates. [#30](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/30)
-   introduces defensive exception handling around database operations in several route and worker files. [#32](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/32)
-   introduces a file-based cancellation mechanism for jobs to improve cross-process cancellation detection, alongside general import cleanups and test formatting. [#34](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/34)

-   introduces a periodic database cancellation check for background jobs, refactors job cancellation routes to centralize authorization and lookup logic, and updates templates to use shared macros with customizable columns. [#35](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/35)
-   Improved redirect worker behavior to maintain page content integrity during link updates. [#36](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/36)
-   Better MediaWiki link normalization and improved auth/session handling to reduce failed edits and login errors. [#37](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/37)
-   More reliable login/callback persistence and safer cleanup when users or tokens are removed. Job audit history preserved when user accounts are deleted. [#38](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/38)
-   Improved database initialization error handling with clearer error reporting. [#39](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/39)
-   Refactor internal functions and add explicit module exports. [#40](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/40)
-   Fixed trailing whitespace issues in generated medical content sections. Corrected navigation link routing for the Medical Content Updater tool. [#41](https://github.com/Mdwiki-TD/mdwiki.org_scripts/pull/41)
