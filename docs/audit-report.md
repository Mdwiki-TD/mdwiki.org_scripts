# Audit Report

**Commit**: `ae22352`
**Date**: 2026-06-14
**Scope**: Full repo, standard effort
**Not audited**: `_works_files/` (archived code), `toolforge_tool/shs/` (deployment scripts, lightly reviewed), frontend templates beyond security-relevant aspects.

---

## Vetted Findings

| #   | Finding                                                                                                                                                                       | Category  | Impact | Effort | Risk | Evidence                                                                       |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------ | ------ | ---- | ------------------------------------------------------------------------------ |
| 1   | **Missing authorization on job deletion route** — `@admin_required` is commented out; any anonymous POST can delete any job                                                   | Security  | HIGH   | S      | LOW  | `src/main_app/app_routes/public_jobs.py:285-290`                               |
| 2   | **State-changing wiki edit via GET bypasses CSRF** — `/newupdater/save/<title>` triggers a live wiki edit on GET; `@oauth_required` only checks session, which CSRF satisfies | Security  | HIGH   | M      | MED  | `src/main_app/app_routes/newupdater/route.py:73-88`                            |
| 3   | **DB password double-encoded in SQLAlchemy URI** — `quote_plus()` applied before `URL.create()` which encodes internally; passwords with `@#%/` break in production           | Bug       | HIGH   | S      | LOW  | `src/main_app/config/flask_config.py:19`                                       |
| 4   | **Rate limiter bypass via forged X-Forwarded-For** — no ProxyFix middleware; attacker rotates IPs to bypass login/callback rate limits                                        | Security  | MED    | S      | LOW  | `src/main_app/app_routes/auth/routes.py:58-62`                                 |
| 5   | **Unauthenticated access to job result files** — `/public_jobs/job-file/<result_file>` serves operational data with no auth check                                             | Security  | MED    | S      | LOW  | `src/main_app/app_routes/public_jobs.py:292-297`                               |
| 6   | **Open redirect via unvalidated `post_login_redirect`** — `request.url` stored in session, redirected to after OAuth without domain validation                                | Security  | MED    | S      | LOW  | `src/main_app/app_routes/auth/utils.py:81`, `auth/routes.py:176`               |
| 7   | **Exception `repr()` leaked to users via flash** — internal paths, DB strings exposed                                                                                         | Security  | MED    | S      | LOW  | `src/main_app/app_routes/fixred.py:62`, `newupdater/route.py:48`               |
| 8   | **`raise exc` loses original traceback** in `db_guard_rollback`                                                                                                               | Bug       | MED    | S      | LOW  | `src/main_app/db/services/utils.py:28,31`                                      |
| 9   | **Missing None check for `site` in fixred_one.py** — `get_user_site()` can return None, passed directly to `MwClientPage`                                                     | Bug       | MED    | S      | LOW  | `src/main_app/shared/fixred_one.py:35-37`                                      |
| 10  | **Job reported "completed" when `before_run()` fails** — `after_run()` coerces pending→completed unconditionally                                                              | Bug       | MED    | S      | LOW  | `src/main_app/jobs_workers/base_worker_object.py:127-132,259-263`              |
| 11  | **CSRF token leaked into background job args** — `request.form.to_dict()` includes `csrf_token`, persisted in job result files                                                | Security  | MED    | S      | LOW  | `src/main_app/app_routes/public_jobs.py:273`                                   |
| 12  | **`is_job_cancelled` issues redundant double-query** — `query().first()` then `session.refresh()` on same row; called every 10 edits                                          | Perf      | MED    | S      | LOW  | `src/main_app/db/services/jobs_service.py:92-95`                               |
| 13  | **O(n\*m) list scan in add_rtt_template** — `x not in template_pages` on two lists of ~30K titles each                                                                        | Perf      | MED    | S      | LOW  | `src/main_app/jobs_workers/public_jobs_workers/add_rtt_template/worker.py:115` |
| 14  | **`DevelopmentConfig` sets `TESTING=True`** — enables exception propagation; dangerous if accidentally deployed                                                               | Security  | LOW    | S      | LOW  | `src/main_app/config/flask_config.py:117-118`                                  |
| 15  | **Worker `_process_one` page-edit pipeline duplicated across 6 workers**                                                                                                      | Tech debt | MED    | M      | MED  | 6 worker files                                                                 |
| 16  | **Worker `process()` main loop duplicated across 8 workers**                                                                                                                  | Tech debt | MED    | M      | MED  | 8 worker files                                                                 |
| 17  | **`start_job` and `start_job_cli` near-duplicate** (50 lines each)                                                                                                            | Tech debt | LOW    | S      | LOW  | `src/main_app/jobs_workers/jobs_worker.py:98-201`                              |
| 18  | **Coverage reporting disabled in pytest.ini** — `--cov` line commented out, report flags inert                                                                                | DX        | LOW    | S      | LOW  | `pytest.ini:19`                                                                |
| 19  | **`src/app1.py` gitignored** — dev entry point excluded from VCS; onboarding blocker                                                                                          | DX        | MED    | S      | LOW  | `.gitignore:8`                                                                 |
| 20  | **CI pipeline fragmented** — lint and tests in separate workflows, no combined gate                                                                                           | DX        | MED    | S      | LOW  | `.github/workflows/ci.yaml`, `pytest.yaml`                                     |
| 21  | **Dead dependency: `tqdm`** in requirements.txt, zero imports in `src/`                                                                                                       | Deps      | LOW    | S      | LOW  | `requirements.txt:15`                                                          |
| 22  | **`requires-python >= 3.10`** conflicts with all tooling targeting 3.13                                                                                                       | Deps      | LOW    | S      | LOW  | `pyproject.toml:6`                                                             |
| 23  | **Dead code: `has_active_job`** exported but never called                                                                                                                     | Tech debt | LOW    | S      | LOW  | `src/main_app/db/services/jobs_service.py:233-251`                             |
| 24  | **Hardcoded fallback username** in import_history worker                                                                                                                      | Bug       | LOW    | S      | LOW  | `src/main_app/jobs_workers/public_jobs_workers/import_history/worker.py:155`   |

---

## Direction Findings

1. **Stub worker `add_unlinkedwikibase` visible to users but does nothing** — registered in the UI, users can start a no-op job. Either gate it behind `ready=False` enforcement or remove from the registry. (`workers_list_public.py:23-30`, `add_unlinkedwikibase/worker.py:38-50`)

2. **12 test files are stubs with only "TODO: write tests"** — critical modules (config, admin service, app factory, route init) have zero coverage despite test files existing. Highest priority: `test_flask_config.py`, `test_admin_service.py`, `test_routes_utils.py`.

3. **`users_table_split.md` plan is ready but unexecuted** — the FK constraint issue it solves (logout deletes user record because `admin_users` and `jobs` reference `user_tokens`) is a real production problem. The plan has migration SQL and code changes across 13+ files.

4. **Worker deduplication is the highest-leverage architectural win** — findings #15 and #16 together mean ~200 lines of near-identical code across 8 workers. Extracting a template method into `BaseObjectsJobWorker` would make future worker development dramatically cheaper.

---

## Dependency Ordering

-   Security findings #1, #4, #5, #6, #7, #11, #14 are all independent S-effort fixes — can be done in any order.
-   Finding #2 (CSRF-via-GET) requires design thought due to the MediaWiki sidebar integration — plan before implementing.
-   Worker deduplication (#15, #16) should follow characterization tests for workers (direction finding #2).
-   Finding #3 (double-encoded password) should be fixed before any DB migration work.

---

## Detailed Evidence

### Finding 1: Missing authorization on job deletion route

```python
# src/main_app/app_routes/public_jobs.py:285-290
# @admin_required  <-- COMMENTED OUT
@self.bp.post("/<string:job_type>/<int:job_id>/delete")
def delete_job(job_type: str, job_id: int) -> Response:
    if job_type not in self.jobs_data_infos:
        abort(404)
    return _delete_job(job_id, job_type)
```

`_delete_job()` (lines 77-93) performs no auth check. Any anonymous POST can cancel and delete any job.

### Finding 2: State-changing wiki edit via GET bypasses CSRF

```python
# src/main_app/app_routes/newupdater/route.py:73-88
@bp_newupdater.route("/save/<path:title>", methods=["GET"])
@oauth_required
def auto_save(title: str) -> str:
    title = _parse_title(title)
    return _newupdater(title, True)  # save=True triggers live wiki edit
```

CSRF protection (`flask_config.py:60`) only covers `["POST", "PUT", "PATCH", "DELETE"]`. A cross-origin `<img src="...">` tag can trigger this. The route is referenced from the MDWiki sidebar (`route.py:78-79`).

### Finding 3: DB password double-encoded

```python
# src/main_app/config/flask_config.py:19
password = quote_plus(db_config.db_password or "")  # first encoding
url = URL.create(
    "mysql+pymysql",
    password=password,  # URL.create encodes again internally
    ...
).render_as_string(hide_password=False)
```

`URL.create()` handles URL encoding of components. Pre-encoding with `quote_plus()` causes double-encoding for passwords containing `@`, `#`, `%`, `/`, etc.

### Finding 4: Rate limiter bypass via forged X-Forwarded-For

```python
# src/main_app/app_routes/auth/routes.py:58-62
def _client_key() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "anonymous"
```

No `ProxyFix` middleware configured in `create_app()`. Attacker sends different `X-Forwarded-For` per request to bypass rate limits.

### Finding 5: Unauthenticated access to job result files

```python
# src/main_app/app_routes/public_jobs.py:292-297
@self.bp.get("/job-file/<string:result_file>")
@self.bp.get("/job-file/<string:result_file>/<string:job_type>")
def read_job_result_file(result_file: str, job_type: str = "") -> ResponseReturnValue:
    result_data = load_job_result(result_file)
    return jsonify(result_data)
```

No auth decorator. Job result files contain operational data (page titles, error messages, revision IDs).

### Finding 6: Open redirect via unvalidated post_login_redirect

```python
# src/main_app/app_routes/auth/utils.py:81
session["post_login_redirect"] = request.url  # full URL including scheme+host

# src/main_app/app_routes/auth/routes.py:176
response = make_response(redirect(session.pop("post_login_redirect", url_for("main.index"))))
```

No validation that the redirect target is same-origin. Combined with Finding #4 (no ProxyFix), `request.url` can be manipulated via Host header.

### Finding 7: Exception repr() leaked to users

```python
# src/main_app/app_routes/fixred.py:62
flash(f"Error processing {title!r}: {exc!r}", "danger")

# src/main_app/app_routes/newupdater/route.py:48
flash(f"Error processing {title!r}: {exc!r}", "danger")
```

`repr()` of exceptions can contain internal paths, DB connection strings, API details.

### Finding 8: `raise exc` loses original traceback

```python
# src/main_app/db/services/utils.py:26-31
except IntegrityError as exc:
    db.session.rollback()
    raise exc  # creates new traceback rooted here
except Exception as exc:
    db.session.rollback()
    raise exc  # same issue
```

Should be bare `raise` to preserve the original call stack.

### Finding 9: Missing None check for site in fixred_one.py

```python
# src/main_app/shared/fixred_one.py:35-37
site = get_user_site(user.to_auth_payload())  # can return None
page = MwClientPage(title, site)  # site=None crashes on page.get_text()
```

Sibling module `newupdater_service.py:43-45` correctly checks for None and returns early.

### Finding 10: Job reported "completed" when before_run() fails

```python
# src/main_app/jobs_workers/base_worker_object.py:259-263
try:
    if not self.before_run():
        return self.result.to_json()  # early return, but...
    self.result = self.process()
except Exception as e:
    self.handle_error(e)
finally:
    self.after_run()  # always runs, and...

# lines 127-132
final_status = self.result.status or "completed"
if final_status in ["running", "pending"]:
    final_status = "completed"  # coerces to "completed" even when before_run failed
```

### Finding 11: CSRF token leaked into job args

```python
# src/main_app/app_routes/public_jobs.py:273
args = request.form.to_dict()  # includes csrf_token field
job_id = _start_job(job_type, args)  # passed to background worker and persisted in result files
```

### Finding 12: Redundant double-query in is_job_cancelled

```python
# src/main_app/db/services/jobs_service.py:92-95
record = db.session.query(JobRecord).filter(...).first()  # fresh SELECT
if record:
    db.session.refresh(record)  # redundant second SELECT on same row
    return record.status == "cancelled"
```

Called every 10 edits via `check_cancel_db_periodic()`.

### Finding 13: O(n\*m) list scan

```python
# src/main_app/jobs_workers/public_jobs_workers/add_rtt_template/worker.py:115
pages_to_add = [x for x in mdwiki_pages if x not in template_pages]
# Both lists ~30K entries; should be set(template_pages) for O(n+m)
```

### Finding 14: DevelopmentConfig sets TESTING=True

```python
# src/main_app/config/flask_config.py:117-118
class DevelopmentConfig(Config):
    DEBUG: bool = True
    TESTING: bool = True  # should only be in TestingConfig
```

### Finding 24: Hardcoded fallback username

```python
# src/main_app/jobs_workers/public_jobs_workers/import_history/worker.py:155
username = self.site.username or "Mr._Ibrahem"
```

---

## Considered and Rejected

-   **`mwoauth` unmaintained**: flagged by subagent but the library is feature-complete for OAuth 1.0a and its dependency chain (`oauthlib`, `requests-oauthlib`) is actively maintained. Not worth the migration cost at this time.
-   **`_works_files/` dead weight**: confirmed but low-impact; removal is a housekeeping task, not an improvement.
-   **Three import paths for `get_user_site`**: cosmetic inconsistency, no runtime impact. Low priority.
-   **Dead config `CorsConfig`/`CORS_DISABLED`**: true but trivially low-impact; not worth a standalone plan.
-   **`colorlog` as required dep**: minor hygiene issue, not worth a plan.
-   **`sys.argv` check in `fixref_text_new.py`**: real but changing behavior risks altering wikitext output for 20K+ pages; needs domain review first.
