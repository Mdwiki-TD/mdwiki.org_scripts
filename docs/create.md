# Repository Comparison Report

## Executive Summary

This report provides a detailed comparison between `mdwiki.org_scripts` and `svg_translate_web`. Both repositories share a common architectural foundation based on Flask, SQLAlchemy, and a background job worker system.

*   **Overall Similarity Estimate**: ~75-80% across the core framework and shared services.
*   **Major Duplication Areas**: Core infrastructure (database models for users/jobs, authentication, configuration management, and admin interface) is highly duplicated, often identical.
*   **High-value Consolidation Opportunities**: Merging the `core`, `db`, and `shared/auth` modules into a shared library would reduce maintenance by ~40%.
*   **Expected Maintenance Reduction Benefits**: Standardizing the common framework allows security patches and feature improvements (like better job monitoring) to be applied once for both tools.
*   **Risks and Blockers**: The repositories have diverged in their specific business logic (medical content vs. SVG translation). The primary risk is breaking tool-specific routes during consolidation of the shared `main_app` structure.

---

## Folder: admin

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_\_init\_\_.py | 100.0% | Identical | Core admin blueprint initialization. | None | Merge directly |
| decorators.py | 100.0% | Identical | Admin access decorators. | None | Merge directly |
| route.py | 96.6% | Imports | Extra imports for new modules in SVG repo. | Extract route registration to a separate config. | Merge with minimal changes |
| routes/\_\_init\_\_.py | 68.8% | Imports | Different module registrations for tool-specific admin tasks. | Standardize registration pattern using a plugin-like system. | Keep separate / Manual merge |
| routes/coordinators.py | 100.0% | Identical | Management of tool coordinators. | None | Merge directly |
| routes/jobs.py | 100.0% | Identical | Admin view for background jobs. | None | Merge directly |
| routes/settings.py | 100.0% | Identical | Global app settings management. | None | Merge directly |
| routes/users.py | 100.0% | Identical | User management. | None | Merge directly |
| sidebar.py | 74.8% | UI items | Different menu items for specific tools. | Use a configuration-based sidebar generation. | Keep separate / Manual merge |

---

## Folder: api_services

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| README.md | 100.0% | Identical | Documentation of API services. | None | Merge directly |
| \_\_init\_\_.py | 86.8% | Imports | Extra exports in SVG repo for file services. | Unified exports for common services. | Minor refactoring |
| category.py | 100.0% | Identical | Wiki category traversal logic. | None | Merge directly |
| clients/\_\_init\_\_.py | 91.4% | Imports | OWID client present in SVG repo. | Use conditional imports or a registry. | Minor refactoring |
| clients/commons_client.py | 100.0% | Identical | Wikimedia Commons API client. | None | Merge directly |
| clients/wiki_client.py | 100.0% | Identical | Generic Wiki API client. | None | Merge directly |
| mwclient_page/\_\_init\_\_.py | 100.0% | Identical | Wrapper for mwclient. | None | Merge directly |
| mwclient_page/mwclient_error.py | 100.0% | Identical | Error handling for mwclient. | None | Merge directly |
| mwclient_page/mwclient_wraper.py | 100.0% | Identical | Advanced mwclient operations. | None | Merge directly |
| query_api.py | 96.0% | Functions | Extra helper functions in SVG repo for metadata. | Merge helpers into a common Wiki utility module. | Merge with minimal changes |

---

## Folder: public

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_\_init\_\_.py | 72.1% | BP registration | Different set of tool-specific blueprints registered. | Implement dynamic blueprint discovery. | Keep separate / Manual merge |
| auth/\_\_init\_\_.py | 100.0% | Identical | Public auth routes init. | None | Merge directly |
| auth/rate_limit.py | 100.0% | Identical | Flask-Limiter setup. | None | Merge directly |
| auth/routes.py | 100.0% | Identical | Login/Logout routes. | None | Merge directly |
| auth/utils.py | 100.0% | Identical | Auth-related helpers. | None | Merge directly |
| jobs_routes_utils.py | 100.0% | Identical | Helpers for job-related routes. | None | Merge directly |
| main_routes/\_\_init\_\_.py | 100.0% | Identical | Main routes init. | None | Merge directly |
| main_routes/routes.py | 87.7% | Routes | SVG repo has more explorer routes. | Split generic routes from tool-specific ones. | Minor refactoring |
| profile.py | 86.3% | Imports | Minimal difference in imports. | Clean up unused imports. | Minor refactoring |
| public_jobs.py | 90.9% | Logic | Specific job handling logic. | Move tool-specific job logic to separate modules. | Minor refactoring |
| utils/\_\_init\_\_.py | 100.0% | Identical | Utility init. | None | Merge directly |
| utils/routes_utils.py | 100.0% | Identical | URL/Route helpers. | None | Merge directly |

---

## Folder: config

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_\_init\_\_.py | 100.0% | Identical | Config init. | None | Merge directly |
| classes.py | 97.2% | Paths dataclass | Extra paths for SVG storage in SVG repo. | Use a more flexible Path dataclass or configuration. | Merge with minimal changes |
| flask_config.py | 100.0% | Identical | Flask app configuration. | None | Merge directly |
| main_settings.py | 92.3% | Settings | Different salts, domains, and UA strings. | Move all environment-specific strings to `.env`. | Minor refactoring |

---

## Folder: core

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_\_init\_\_.py | 100.0% | Identical | Core module init. | None | Merge directly |
| cookies/\_\_init\_\_.py | 100.0% | Identical | Cookie management init. | None | Merge directly |
| cookies/cookie.py | 100.0% | Identical | JWT/Cookie handling logic. | None | Merge directly |
| cookies/cookie_header_client.py | 100.0% | Identical | Cookie parsing helpers. | None | Merge directly |
| crypto.py | 100.0% | Identical | Encryption/Decryption utilities. | None | Merge directly |
| jinja_filters.py | 100.0% | Identical | Custom Jinja2 filters. | None | Merge directly |

---

## Folder: db/models

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_\_init\_\_.py | 64.7% | Model exports | SVG repo has many more tool-specific models. | Use a discovery mechanism for models. | Keep separate / Manual merge |
| jobs.py | 100.0% | Identical | Background job database model. | None | Merge directly |
| settings.py | 100.0% | Identical | App settings database model. | None | Merge directly |
| users.py | 93.2% | Formatting | Minor whitespace and formatting diffs. | Reformat to match a standard. | Minor refactoring |

---

## Folder: db/services

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_\_init\_\_.py | 74.6% | Service exports | Different service set for each tool. | Standardize service registration. | Keep separate / Manual merge |
| admin_service.py | 100.0% | Identical | Database services for admin tasks. | None | Merge directly |
| delete_service.py | 90.5% | Functions | SVG repo includes file system deletion. | Abstract storage deletion from DB deletion. | Minor refactoring |
| jobs_service.py | 100.0% | Identical | Database services for job tracking. | None | Merge directly |
| settings_service.py | 100.0% | Identical | Database services for settings. | None | Merge directly |
| user_token_service.py | 100.0% | Identical | Token management services. | None | Merge directly |
| users_service.py | 100.0% | Identical | User-related database operations. | None | Merge directly |
| utils/\_\_init\_\_.py | 100.0% | Identical | DB utility init. | None | Merge directly |
| utils/db_guard_model.py | 100.0% | Identical | DB session protection. | None | Merge directly |
| utils/retry_on_disconnect.py | 100.0% | Identical | DB connection resilience logic. | None | Merge directly |

---

## Folder: shared

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_\_init\_\_.py | 100.0% | Identical | Shared module init. | None | Merge directly |
| auth/auth_service.py | 100.0% | Identical | High-level auth logic. | None | Merge directly |
| auth/auth_users_service.py | 100.0% | Identical | Auth logic tied to user model. | None | Merge directly |
| auth/current_user.py | 100.0% | Identical | Current user session management. | None | Merge directly |
| auth/mwoauth_handshake.py | 94.1% | Logic | Extra error handling and state in SVG repo. | Adopt the SVG repo's more robust version. | Minor refactoring |
| decode_bytes.py | 100.0% | Identical | Byte-to-string utilities. | None | Merge directly |

---

## Folder: su_services

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_\_init\_\_.py | 100.0% | Identical | SU services init. | None | Merge directly |
| jobs_files_service.py | 96.6% | Paths | SVG repo uses specific relative paths. | Use `pathlib` for environment-agnostic paths. | Merge with minimal changes |

---

## Folder: templates

| File Name | Match % | Differences | Notes | Recommended Modifications | Merge Recommendation |
| --------- | ------- | ----------- | ----- | ------------------------- | -------------------- |
| \_macros.html | 100.0% | Identical | UI macros. | None | Merge directly |
| \_macros/\_jobs_macros.html | 100.0% | Identical | Job UI macros. | None | Merge directly |
| \_macros/forms.html | 100.0% | Identical | Form UI macros. | None | Merge directly |
| \_navbar.html | 79.0% | Menu items | Different tools in navbar. | Implement a dynamic, config-driven navbar. | Keep separate / Manual merge |
| admins/\_sidebar.html | 100.0% | Identical | Admin sidebar sub-template. | None | Merge directly |
| admins/admin.html | 100.0% | Identical | Main admin page. | None | Merge directly |
| admins/base1.html | 100.0% | Identical | Admin base template. | None | Merge directly |
| admins/coordinators.html | 100.0% | Identical | Coordinator management template. | None | Merge directly |
| admins/popup_action.html | 100.0% | Identical | Admin popup template. | None | Merge directly |
| admins/settings.html | 99.2% | Formatting | Whitespace differences. | Reformat to common style. | Merge with minimal changes |
| admins/users.html | 81.9% | UI | SVG repo has a more detailed user list. | Synchronize the more feature-rich UI. | Minor refactoring |
| base.html | 97.3% | Titles | Specific page titles in SVG repo. | Use generic variables with defaults. | Merge with minimal changes |
| error.html | 100.0% | Identical | Error display template. | None | Merge directly |
| index.html | 19.5% | Content | Completely different homepages for each tool. | Keep tool-specific homepages separate. | Keep separate |
| index_db_error.html | 100.0% | Identical | DB error landing page. | None | Merge directly |
| jobs_templates/\_help_templates/\_job_summary.html | 100.0% | Identical | Job help summary. | None | Merge directly |
| jobs_templates/\_help_templates/\_skipped_table.html | 98.3% | Formatting | Minor formatting diffs. | Reformat. | Merge with minimal changes |
| jobs_templates/base_details_public.html | 100.0% | Identical | Job details base template. | None | Merge directly |
| jobs_templates/base_list_public.html | 100.0% | Identical | Job list base template. | None | Merge directly |
| profile.html | 97.7% | Formatting | Minor formatting diffs. | Reformat. | Merge with minimal changes |

---

## Consolidation Opportunities

### Priority 1 (Immediate Merge Candidates)
*   **`src/main_app/core/`**: All files are identical.
*   **`src/main_app/shared/auth/`**: Highly identical, provides standard OAuth flow.
*   **`src/main_app/db/services/`**: Core services (`jobs_service`, `users_service`) are identical.

### Priority 2 (Minor Refactoring Required)
*   **`src/main_app/config/main_settings.py`**: Needs to move environment-specific strings (User-Agent, Cookie Names) to variables.
*   **`src/main_app/db/models/users.py`**: Just needs consistent formatting.
*   **`src/main_app/su_services/jobs_files_service.py`**: Needs standardizing on `pathlib`.

### Priority 3 (Shared Abstractions Recommended)
*   **Admin Sidebar/Navbar**: Refactor to use a configuration list rather than hardcoded HTML links.
*   **`public_jobs.py`**: Abstract the job start logic to be tool-agnostic.

---

## Database Layer Analysis

*   **Models**: Both repos use the same `User`, `UserToken`, `JobRecord`, and `Setting` models. `svg_translate_web` adds several models for OWID charts and templates.
*   **ORM Patterns**: Both use SQLAlchemy with the same session management and `BaseModel` inheritance.
*   **Query Logic**: Identical for common entities.
*   **Opportunity**: Create a `mdwiki-common-db` package containing all shared models and services. Tool-specific models can then inherit from or extend this common layer.

---

## Synchronization Strategy

| Merge Candidate | Target Repository | Source Repository | Required Changes | Effort | Risk |
| --------------- | ----------------- | ----------------- | ---------------- | ------ | ---- |
| Core Framework | Shared Library | Both | Extract `core`, `crypto`, `cookies` | Medium | Low |
| Auth Services | Shared Library | `svg_translate_web` | Use the more robust version from SVG | Medium | Medium |
| Admin UI | Shared Library | Both | Refactor sidebar to be data-driven | Medium | Low |
| Config System | Shared Library | Both | Externalize all constants to `.env` | Low | Low |

---

## Final Recommendations

1.  **Shared Package**: Create a new repository or directory (e.g., `mdwiki-flask-base`) to house the `core`, `db/models` (shared), `db/services` (shared), `shared/auth`, and common templates.
2.  **Specific Logic**: Keep `src/main_app/public/newupdater` (mdwiki) and `src/main_app/public/main_routes/explorer_routes` (svg) in their respective repositories.
3.  **Estimated Maintenance Reduction**: **~35-40%**. Security updates for OAuth and job processing would only need to be done once.
4.  **Architecture**: Move towards a "Core + Plugins" architecture where the tool-specific logic is injected into the core framework via blueprints and configuration.
5.  **Phased Migration**:
    *   **Phase 1**: Standardize `core` and `auth` modules (100% matches).
    *   **Phase 2**: Refactor `config` and `db/services` to be environment-aware.
    *   **Phase 3**: Implement the dynamic UI (Sidebar/Navbar).
    *   **Phase 4**: Extract the shared code into a common dependency.
