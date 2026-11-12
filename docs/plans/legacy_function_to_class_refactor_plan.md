# Legacy Function-to-Class Refactoring Plan

## Overview

This plan covers the refactoring of standalone functions across the `main_app` package into cohesive, well-layered class-based designs, while preserving backward compatibility through thin legacy wrappers.

**Base path:** `www/python/src/main_app/`

---

## Scope Assessment

After analyzing all 150+ Python files in `main_app`, the codebase is **already partially class-based** (auth services, database CRUD, HTTP clients, etc.). The remaining standalone functions cluster into a small number of modules that genuinely benefit from consolidation.

### Already Class-Based (No Refactor Needed)

These modules are already well-structured as classes and need no changes:

| Module | Current Structure |
|--------|------------------|
| `api_services/clients/http_client.py` | `HttpClient` class |
| `api_services/clients/http_client_helper.py` | `HttpHelper` class |
| `api_services/clients/wikisite_client.py` | `WikiSiteClient` class |
| `api_services/clients/toolforge_api_service.py` | `ToolforgeApiService` class |
| `api_services/clients/toolforge_jobs_api_service.py` | `ToolforgeJobsService` class |
| `api_services/citation_api.py` | `CitationApi` class |
| `api_services/enwiki_api.py` | `EnwikiApi` class |
| `api_services/mwclient_page/mwclient_wraper.py` | `MwClientPage` class |
| `services/auth/auth_service.py` | `OAuthService` class |
| `services/auth/flow.py` | `AuthFlowService` class |
| `services/auth/current_user.py` | `CurrentUser` dataclass |
| `services/auth/current_user_resolver.py` | `CurrentUserResolver` class |
| `services/auth/token_manager.py` | `TokenManager` class |
| `services/core/crypto.py` | `CryptoService` class |
| `services/core/cookies/signing.py` | `SignedTokenService` class |
| `database/services/crud_service.py` | `CRUDService` generic class |
| `database/services/jobs_service.py` | `JobsService` class |
| `database/services/error_log_service.py` | `ErrorLogService` class |
| `database/services/users/users_service.py` | `UsersService` class |
| `database/services/users/user_token_service.py` | `UserTokenService` class |
| `database/services/users/admin_service.py` | `AdminService` class |
| `database/services/settings_service.py` | `SettingsService` class (minor: 2 standalone helpers) |
| `templates_markups/navbar/nav_bar.py` | `NavigationBar` class |
| `templates_markups/sidebar/sidebar.py` | `Sidebar` class |
| `admin/routes_services/toolforge_jobs_service.py` | `JobsPageService` class |
| `public/shared_jobs_routes.py` | `SharedJobRoutes` class |
| `services/shared_classes.py` | `UpdaterTextOutcome` dataclass |
| `config/classes.py` | Dataclass-based config |
| `decorators/` | Decorators (appropriate as functions) |

---

## Files to Change

### Group 1: `api_services/query_api.py` → `MediaWikiQueryService` class

**Current state:** 8 standalone functions, all taking `site: Site` as a parameter.

**Functions:**
- `get_template_pages(title, site, namespace)`
- `is_pages_exists(titles, site)`
- `resolve_redirects(titles, site)`
- `search_pages(query, site, namespace, limit)`
- `get_double_redirects(site)`
- `get_page_links(title, site, namespace)`
- `get_category_members_titles(site, category_name, namespace)`
- `import_page_from_wiki(site, title, family)`

**Target:** Single `MediaWikiQueryService` class with `site` injected via `__init__`.

**Files to modify:**
- `api_services/query_api.py` — refactor functions into class, add legacy wrappers
- Callers that import from `query_api` (search repo for usages)

**Complexity:** Medium. All functions share the same `site` collaborator, making this a natural class boundary.

---

### Group 2: `api_services/category.py` → merge into `MediaWikiQueryService`

**Current state:** 1 standalone function `get_category_members(site, category_title, namespace, limit)`.

**Target:** Move into `MediaWikiQueryService` as a method. Keep legacy wrapper in `category.py`.

**Files to modify:**
- `api_services/category.py` — add legacy wrapper importing from `query_api`
- `api_services/query_api.py` — add `get_category_members` method

---

### Group 3: `services/replace_wikilink/__init__.py` → `WikilinkReplacer` class

**Current state:** 2 public standalone functions + 2 private helpers.

**Functions:**
- `_normalize_mediawiki_title(title)` (private)
- `_replace_wikilink_destinations(text, redirect_to, final_target, set_text)` (private)
- `replace_wikilink_destinations(text, redirect_to, final_target)`
- `replace_wikilink_redirects(text, redirect_to, final_target)`

**Target:** `WikilinkReplacer` class with static/class methods (pure functions on text, no I/O).

**Files to modify:**
- `services/replace_wikilink/__init__.py` — refactor into class, add legacy wrappers

**Complexity:** Low. Pure functions, no external dependencies.

---

### Group 4: `services/fixref_shared/fixref_text_new.py` → `FixRefTextService` class

**Current state:** 3 standalone functions operating on wikitext.

**Functions:**
- `change_lay_source(temp)` → returns `(str, Template)`
- `add_title(temp)` → returns `Template`
- `fix_ref_template(text, returnsummary)` → returns `str | tuple[str, str]`

**Target:** `FixRefTextService` class. `change_lay_source` and `add_title` become private methods; `fix_ref_template` is the public entry point.

**Files to modify:**
- `services/fixref_shared/fixref_text_new.py` — refactor into class, add legacy wrappers

**Complexity:** Low-Medium. Functions call `make_title` (external), but otherwise self-contained.

---

### Group 5: `services/fixref_shared/make_title_bot.py` → `TitleMaker` class

**Current state:** 1 cached function `make_title(url)` with module-level regex and `CitationApi` dependency.

**Target:** `TitleMaker` class with `CitationApi` injected via `__init__`. The `lru_cache` moves to the instance or is replaced with an instance-level cache.

**Files to modify:**
- `services/fixref_shared/make_title_bot.py` — refactor into class, add legacy wrapper

**Complexity:** Low. Single function with one collaborator.

---

### Group 6: `services/fixref_shared/fixred_worker.py` → `FixRedirectWorker` class

**Current state:** 3 standalone functions.

**Functions:**
- `_replace_links(text, oldlink, newlink)` (private)
- `replace_in_text(text, new_targets)`
- `work_on_text(title, text, site, state)`

**Target:** `FixRedirectWorker` class with a `MediaWikiQueryService` (from Group 1) injected. `work_on_text` becomes the main public method.

**Files to modify:**
- `services/fixref_shared/fixred_worker.py` — refactor into class, add legacy wrappers

**Complexity:** Medium. Depends on `query_api` functions and `replace_wikilink`.

---

### Group 7: `services/named_param/__init__.py` → `NamedParamEditor` class

**Current state:** 2 standalone functions.

**Functions:**
- `gt_arg(temp, name)` (helper)
- `add_param_named(text)` (main)

**Target:** `NamedParamEditor` class. Pure wikitext transformation, no I/O.

**Files to modify:**
- `services/named_param/__init__.py` — refactor into class, add legacy wrappers

**Complexity:** Low. Pure functions.

---

### Group 8: `services/newupdater_service.py` → `NewUpdaterService` class

**Current state:** 1 standalone function `newupdater_one_title(title, save, summary, user)`.

**Target:** `NewUpdaterService` class with collaborators injected (`WikiSiteClient`, etc.).

**Files to modify:**
- `services/newupdater_service.py` — refactor into class, add legacy wrapper

**Complexity:** Low. Single function, but orchestrates multiple collaborators.

---

### Group 9: `public/routes_service/fixred_one.py` → `FixRedOneService` class

**Current state:** 1 standalone function `work_on_title(title, save, summary, user)`.

**Target:** `FixRedOneService` class wrapping `FixRedirectWorker` (from Group 6).

**Files to modify:**
- `public/routes_service/fixred_one.py` — refactor into class, add legacy wrapper

**Complexity:** Low. Thin orchestration layer.

---

### Group 10: `io/jobs_files_service.py` → `JobFilesService` class

**Current state:** 6 standalone functions for file I/O.

**Functions:**
- `get_jobs_data_dir()`
- `save_data(result_data, filepath)`
- `save_job_result_by_name(filename, result_data)`
- `load_job_result(filename)`
- `create_job_cancelled_file(filename)`
- `is_job_cancelled_file_exist(filename)`

**Target:** `JobFilesService` class with `base_dir` resolved via settings. File I/O is the core responsibility.

**Files to modify:**
- `io/jobs_files_service.py` — refactor into class, add legacy wrappers
- `io/__init__.py` — update re-exports

**Complexity:** Medium. Multiple functions sharing a directory config.

---

### Group 11: `services/fixref_shared/objects.py` — Review

**Current state:** Likely contains `RunState` dataclass.

**Action:** Verify it's already a dataclass; no refactor needed if so.

**Files to modify:** None (likely already class-based).

---

### Group 12: Minor standalone helpers

These are small, isolated utilities. Per the skill guidance ("keep it simple"), some may be better left as functions or grouped into a small utility class only if they grow.

| File | Functions | Decision |
|------|-----------|----------|
| `utils/verify.py` | `verify_required_fields` | Keep as function (single pure function, no benefit from class) |
| `services/utils/decode_bytes.py` | `coerce_bytes` | Keep as function (single pure function) |
| `services/core/jinja_filters.py` | `get_status_class`, `short_url`, `check_active_route`, `commas_filter`, `to_json_filter`, `is_job_running` | Group into `JinjaFilters` class (already partially done with `FormatTimestamps`); keep `filters` dict |
| `database/services/settings_service.py` | `_serialize_value`, `format_values` | Move into `SettingsService` as static/class methods |
| `logger_config.py` | `prepare_log_file`, `setup_file_handler`, `setup_logging`, `get_log_dir`, `configure_logging` | Group into `LoggingConfigurator` class |
| `error_pages.py` | `safe_headers`, `safe_query`, `client_ip`, `log_error`, `wants_json`, `respond` | Group into `ErrorHandler` class |
| `api_services/clients/wikisite_client.py` | `coerce_encrypted` | Keep as module-level helper (used by `WikiSiteClient`) |

---

## Files NOT Changed

These modules are already well-designed or are inappropriate for class wrapping:

- **`config/`** — Already dataclass-based frozen config. No standalone functions to refactor.
- **`database/models/`** — SQLAlchemy models. Already class-based.
- **`extensions/`** — Flask extension singletons. Appropriate as module-level objects.
- **`decorators/`** — Decorators are naturally functions.
- **`templates_markups/`** — Already class-based (`NavigationBar`, `Sidebar`).
- **`admin/`** — Routes and route services already use classes or are thin controllers.
- **`public/routes/`** — Thin route handlers (controllers). No business logic to extract.
- **`jobs_workers/`** — Already class-based (`BaseWorker` hierarchy).
- **`services/new_updater/`** — Domain-specific medical content logic. Large and complex; refactoring these would be a separate effort beyond the scope of this plan (risk of behavior change is high).

---

## Execution Order

The groups have dependencies. The recommended execution order is:

1. **Group 3** (`WikilinkReplacer`) — No dependencies, pure functions
2. **Group 7** (`NamedParamEditor`) — No dependencies, pure functions
3. **Group 5** (`TitleMaker`) — Depends only on `CitationApi` (already class-based)
4. **Group 1 + 2** (`MediaWikiQueryService`) — Core API layer, used by Groups 6 and 9
5. **Group 4** (`FixRefTextService`) — Depends on Group 5 (`TitleMaker`)
6. **Group 6** (`FixRedirectWorker`) — Depends on Groups 1 and 3
7. **Group 8** (`NewUpdaterService`) — Depends on Group 7
8. **Group 9** (`FixRedOneService`) — Depends on Group 6
9. **Group 10** (`JobFilesService`) — Independent
10. **Group 12** (minor helpers) — Independent, can be done in any order

---

## Complete File List

### Files to Modify (refactor + add legacy wrappers)

| # | File | Change |
|---|------|--------|
| 1 | `api_services/query_api.py` | 8 functions → `MediaWikiQueryService` class + legacy wrappers |
| 2 | `api_services/category.py` | 1 function → move method to `MediaWikiQueryService`, legacy wrapper here |
| 3 | `services/replace_wikilink/__init__.py` | 2+2 functions → `WikilinkReplacer` class + legacy wrappers |
| 4 | `services/fixref_shared/fixref_text_new.py` | 3 functions → `FixRefTextService` class + legacy wrappers |
| 5 | `services/fixref_shared/make_title_bot.py` | 1 function → `TitleMaker` class + legacy wrapper |
| 6 | `services/fixref_shared/fixred_worker.py` | 3 functions → `FixRedirectWorker` class + legacy wrappers |
| 7 | `services/named_param/__init__.py` | 2 functions → `NamedParamEditor` class + legacy wrappers |
| 8 | `services/newupdater_service.py` | 1 function → `NewUpdaterService` class + legacy wrapper |
| 9 | `public/routes_service/fixred_one.py` | 1 function → `FixRedOneService` class + legacy wrapper |
| 10 | `io/jobs_files_service.py` | 6 functions → `JobFilesService` class + legacy wrappers |
| 11 | `io/__init__.py` | Update re-exports to include new class |
| 12 | `services/core/jinja_filters.py` | Group standalone functions into `JinjaFilters` class |
| 13 | `database/services/settings_service.py` | Move `_serialize_value` and `format_values` into `SettingsService` |
| 14 | `logger_config.py` | Group into `LoggingConfigurator` class + legacy wrappers |
| 15 | `error_pages.py` | Group helper functions into `ErrorHandler` class |

### Files to Create

| # | File | Purpose |
|---|------|---------|
| 1 | `tests/unit/test_query_api_refactor.py` | Tests for `MediaWikiQueryService` |
| 2 | `tests/unit/test_wikilink_replacer.py` | Tests for `WikilinkReplacer` |
| 3 | `tests/unit/test_fixref_text_service.py` | Tests for `FixRefTextService` |
| 4 | `tests/unit/test_title_maker.py` | Tests for `TitleMaker` |
| 5 | `tests/unit/test_fix_redirect_worker.py` | Tests for `FixRedirectWorker` |
| 6 | `tests/unit/test_named_param_editor.py` | Tests for `NamedParamEditor` |
| 7 | `tests/unit/test_new_updater_service.py` | Tests for `NewUpdaterService` |
| 8 | `tests/unit/test_job_files_service.py` | Tests for `JobFilesService` |
| 9 | `tests/unit/test_legacy_compat.py` | Equivalence tests: legacy wrappers vs new classes |

### Files NOT Modified

All files listed in "Already Class-Based" and "Files NOT Changed" sections above remain untouched.

---

## Design Decisions

### Why not refactor `services/new_updater/` (bots, lists, chembox, drugbox, etc.)?

These modules contain years of medical-content domain rules encoded as standalone functions. They are complex, interdependent, and untested. Refactoring them in the same pass would:
- Risk behavior changes in critical content-editing logic
- Make it impossible to verify equivalence without characterization tests
- Dramatically increase the scope and risk of this refactor

**Recommendation:** Treat `new_updater/` as a separate future effort, preceded by characterization tests.

### Why keep some functions as functions?

Per the skill guidance: "A few short, pure functions → one small class (or leave as functions if a class adds nothing)." Functions like `verify_required_fields`, `coerce_bytes`, and `coerce_encrypted` are single-purpose utilities where a class wrapper adds ceremony without benefit.

### Legacy wrapper strategy

Every legacy wrapper:
- Preserves the exact original function name, signature, defaults, and return type
- Contains no business logic — delegates immediately to the new class
- Has no deprecation warnings
- Builds default collaborators lazily so old callers need no new arguments

---

## Migration Guide Template

### `query_api` → `MediaWikiQueryService`

| Legacy call | New API | Notes |
|---|---|---|
| `get_template_pages(title, site)` | `MediaWikiQueryService(site=site).get_template_pages(title)` | Construct once per site |
| `is_pages_exists(titles, site)` | `MediaWikiQueryService(site=site).is_pages_exists(titles)` | |
| `resolve_redirects(titles, site)` | `MediaWikiQueryService(site=site).resolve_redirects(titles)` | |
| `search_pages(query, site)` | `MediaWikiQueryService(site=site).search_pages(query)` | |
| `get_double_redirects(site)` | `MediaWikiQueryService(site=site).get_double_redirects()` | |
| `get_page_links(title, site)` | `MediaWikiQueryService(site=site).get_page_links(title)` | |
| `get_category_members_titles(site, name)` | `MediaWikiQueryService(site=site).get_category_members_titles(name)` | |
| `import_page_from_wiki(site, title)` | `MediaWikiQueryService(site=site).import_page_from_wiki(title)` | |
| `get_category_members(site, title)` | `MediaWikiQueryService(site=site).get_category_members(title)` | Moved from `category.py` |

### `replace_wikilink` → `WikilinkReplacer`

| Legacy call | New API | Notes |
|---|---|---|
| `replace_wikilink_destinations(text, old, new)` | `WikilinkReplacer.replace_destinations(text, old, new)` | Static method |
| `replace_wikilink_redirects(text, old, new)` | `WikilinkReplacer.replace_redirects(text, old, new)` | Static method |

### `fixref_text_new` → `FixRefTextService`

| Legacy call | New API | Notes |
|---|---|---|
| `fix_ref_template(text)` | `FixRefTextService().fix_ref_template(text)` | |
| `fix_ref_template(text, returnsummary=True)` | `FixRefTextService().fix_ref_template(text, returnsummary=True)` | |

### `make_title_bot` → `TitleMaker`

| Legacy call | New API | Notes |
|---|---|---|
| `make_title(url)` | `TitleMaker().make_title(url)` | Default `CitationApi` injected |

### `fixred_worker` → `FixRedirectWorker`

| Legacy call | New API | Notes |
|---|---|---|
| `work_on_text(title, text, site, state)` | `FixRedirectWorker(query_service=MediaWikiQueryService(site=site)).work_on_text(title, text, state)` | |
| `replace_in_text(text, targets)` | `FixRedirectWorker().replace_in_text(text, targets)` | |

### `named_param` → `NamedParamEditor`

| Legacy call | New API | Notes |
|---|---|---|
| `add_param_named(text)` | `NamedParamEditor().add_param_named(text)` | |

### `jobs_files_service` → `JobFilesService`

| Legacy call | New API | Notes |
|---|---|---|
| `save_job_result_by_name(name, data)` | `JobFilesService().save_result(name, data)` | |
| `load_job_result(filename)` | `JobFilesService().load_result(filename)` | |
| `create_job_cancelled_file(name)` | `JobFilesService().create_cancel_file(name)` | |
| `is_job_cancelled_file_exist(name)` | `JobFilesService().is_cancel_file_exist(name)` | |

### `newupdater_service` → `NewUpdaterService`

| Legacy call | New API | Notes |
|---|---|---|
| `newupdater_one_title(title, save, summary, user)` | `NewUpdaterService().update_one(title, save, summary, user)` | |

### `fixred_one` → `FixRedOneService`

| Legacy call | New API | Notes |
|---|---|---|
| `work_on_title(title, save, summary, user)` | `FixRedOneService().work_on_title(title, save, summary, user)` | |

---

## Pre-Delivery Checklist

- [ ] All original public functions still exist with identical signatures and defaults
- [ ] Legacy layer contains no duplicated business logic
- [ ] No hidden globals or infrastructure created inside domain logic
- [ ] Every collaborator is an optional `__init__` parameter with a default
- [ ] Collaborators are passed down to child classes instead of being re-created
- [ ] The solution is as simple as the code allows
- [ ] Tests use pytest, are short and simple, and inject fakes through constructors
- [ ] Existing tests pass unchanged
- [ ] New tests cover the normal case, key edge cases, and exceptions
- [ ] No unrelated changes were introduced
- [ ] Comments and docstrings are in English
- [ ] Documentation and migration guide are included
