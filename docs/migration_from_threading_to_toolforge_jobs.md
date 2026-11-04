# Architectural Migration Report: Transitioning from In-Process Threading to Wikimedia Toolforge Jobs API

## 1. Executive Summary

This report provides a comprehensive, phased technical architecture and implementation roadmap for migrating the background job execution subsystem in `mdwiki-org-scripts` from in-process Python `threading` (`src/main_app/jobs_workers/jobs_worker.py`) to the cloud-native Wikimedia Toolforge Jobs framework using the Toolforge Jobs API (`src/main_app/api_services/clients/toolforge_jobs_api_service.py`).

### Context & Motivations
Currently, the application runs background jobs (such as template data extraction, category updates, and batch redirects) as daemon threads directly inside the web service Flask process. While this model is straightforward for local development, in a production Kubernetes environment on Wikimedia Toolforge it introduces severe operational bottlenecks:
1. **Memory & CPU Contention**: Web requests and long-running batch jobs share the same container resources. A memory spike or high CPU workload in a worker thread can cause out-of-memory (OOM) kills of the entire web container, disrupting web users.
2. **Web Process Lifetime Coupling**: When Toolforge restarts, updates, or scales the web container, all in-flight daemon threads are abruptly killed without graceful shutdown or final DB status updates, leaving jobs in a permanent "running" state in the database.
3. **Python GIL & Scalability Limits**: The CPython Global Interpreter Lock (GIL) limits true multi-core utilization for CPU-bound tasks within a single process.
4. **Toolforge Quota & Execution Policy**: Toolforge provides an isolated Kubernetes job execution engine (`jobs-framework`) specifically designed for one-off batch scripts, continuous daemons, and scheduled cron jobs.

### Target Architecture
The proposed architecture decouples job orchestration (web UI / REST API) from job execution:
- The Flask web tier acts purely as a coordinator: creating job records in the database, submitting execution requests to the Toolforge Jobs API (`POST /jobs/v1/tool/{tool}/jobs`), and monitoring status.
- Each background job runs inside an isolated, containerized Kubernetes pod managed by Toolforge Jobs API.
- A unified CLI entry point (`flask run-job`) executes individual jobs by fetching their state and credentials from the shared persistence layer.
- An environment-aware execution backend abstracts the difference between local development (`threading` or local subprocesses) and production deployment (`ToolforgeJobsService`).

---

## 2. In-Depth Analysis of Current Implementation (`jobs_worker.py`)

### 2.1 Threading Execution Lifecycle
The current threading architecture in `src/main_app/jobs_workers/jobs_worker.py` operates as follows:
1. **Job Invocation**: `start_job_form(...)` or `start_job(...)` is called from HTTP route handlers (e.g., `SharedJobRoutes.start_job_handler`).
2. **Database Record Creation**: A new `JobRecord` is created synchronously via `JobsService().create_job(job_type, username)`. If an active job of the same type already exists, `DuplicateRecordError` is raised.
3. **Thread Instantiation**:
   - A `threading.Event()` is created for cancellation tracking and registered in a global in-memory dictionary `JOBS_CANCEL_EVENTS` keyed by `job_id`.
   - A `threading.Thread` targetting `_runner` is spawned with `daemon=True` passing `runner_data: JobsRunner`, the worker class (subclassing `BaseObjectsJobWorker`), and the Flask app reference.
4. **Execution (`_runner`)**:
   - Runs within `with flask_app.app_context():`.
   - Instantiates `worker = target_class(runner_data)` and executes `worker.run()`.
   - In `finally:`, removes the event via `_pop_cancel_event(runner_data.job_id)`.
5. **Lifecycle Hooks in Worker (`BaseObjectsJobWorker`)**:
   - `before_run()` updates database status to `running` and saves initial JSON progress.
   - `process()` performs actual wiki/network operations in batches.
   - `after_run()` sets final status (`completed`, `failed`, or `cancelled`), records completion timestamps, and writes out final JSON results.

### 2.2 Cancellation Architecture
Cancellation is multi-layered:
- **Local (In-Memory)**: If the cancellation request occurs in the same process, `_get_jobs_cancel_event(job_id)` retrieves the `threading.Event` and calls `set()`. The worker checks `self.cancel_event.is_set()` during processing.
- **File Flag**: A sentinel file named `<result_file>.cancelled` is written to disk via `create_job_cancelled_file(...)`. The worker checks `is_job_cancelled_file_exist(...)`.
- **Database Flag**: `JobsService().cancel_job_db(job_id, job_type)` marks the database record as cancelled. The worker periodically checks `self.check_cancel_db_periodic()`.

### 2.3 Limitations & Fragilities of Current Model
- **Process Memory Leaks**: Heavy batch operations accumulating large wikitext or parse trees can trigger memory leaks inside the Gunicorn/uWSGI web process.
- **Process Termination Vulnerability**: If the web pod is restarted by Kubernetes (e.g., due to deployment, health check failure, or resource constraints), all threads die immediately without executing `finally:` blocks or `after_run()`.
- **Global Lock & In-Memory Registry Contention**: The `JOBS_CANCEL_EVENTS` dictionary is tied to a single Python process. If the web service runs multiple workers/pods, in-memory cancellation fails to reach workers across different processes (relying only on DB/file flags).

---

## 3. Analysis of Toolforge Jobs API (`ToolforgeJobsService`)

The new client in `src/main_app/api_services/clients/toolforge_jobs_api_service.py` provides direct access to the Toolforge Jobs REST API (`/jobs/v1`).

### 3.1 Key Endpoints & Capabilities
| API Method | HTTP Route | Purpose | Return Type |
|---|---|---|---|
| `create_job(data)` | `POST /jobs/v1/tool/{tool}/jobs` | Submit and spawn a new Kubernetes Job pod | `JobResponse` |
| `list_jobs(include_unset)` | `GET /jobs/v1/tool/{tool}/jobs` | List all active, queued, or completed jobs | `JobListResponse` |
| `show_job(job_id)` | `GET /jobs/v1/tool/{tool}/jobs/{id}` | Retrieve metadata, container status, exit codes | `JobResponse` |
| `delete_job(job_id)` | `DELETE /jobs/v1/tool/{tool}/jobs/{id}` | Kill/delete a running or queued job | `MessagesResponse` |
| `restart_job(job_id)` | `POST /jobs/v1/tool/{tool}/jobs/{id}/restart` | Trigger immediate re-run of a scheduled/cron job | `MessagesResponse` |
| `get_logs(job_id)` | `GET /jobs/v1/tool/{tool}/jobs/{id}/logs` | Fetch real-time `stdout`/`stderr` pod logs | `str` (plain text) |
| `quotas()` | `GET /jobs/v1/tool/{tool}/quotas` | Verify CPU, memory, and concurrent job quotas | `QuotaResponse` |
| `images()` | `GET /jobs/v1/tool/{tool}/images` | Retrieve supported container images (e.g. `python3.13`) | `ImagesResponse` |

### 3.2 Toolforge Job Data Structure (`NewJob`)
A new one-off job is created by passing a `NewJob` dict:
```python
job_payload: NewJob = {
    "name": "mdw-job-42",                   # 1-52 chars: [a-z0-9]([-a-z0-9]*[a-z0-9])?
    "imagename": "python3.13",              # Standard toolforge image name
    "cmd": "/data/project/mdw/app/bin/run_job.sh 42",  # Executable command line
    "job_type": "one-off",                  # Batch job type
    "memory": "1Gi",                        # Memory reservation (e.g. 512Mi, 1Gi, 2Gi)
    "cpu": "0.5",                           # CPU reservation
    "emails": "none",                       # Notification preference: none, onfailure, all
    "mount": "all",                         # Mount NFS home & project shared storage
    "retry": 0,                             # Do not auto-retry failed one-off jobs
    "filelog": True,                        # Write container logs to files on NFS
    "filelog_stdout": "/data/project/mdw/logs/job-42.out",
    "filelog_stderr": "/data/project/mdw/logs/job-42.err",
}
```

### 3.3 Status Lifecycle in Toolforge Jobs
Toolforge Kubernetes jobs expose both high-level and granular status:
- `job["status"]["short"]`: `pending`, `running`, `succeeded`, `failed`, or `unknown`.
- `job["status"]["duration"]`: Formatted elapsed run duration (e.g. `2m34s`).
- `job["status"]["messages"]`: Pod status diagnostics (e.g., `["exitcode 0"]` or `["exitcode 137 (OOMKilled)"]`).
- `job["status_long"]`: Extended Kubernetes Pod phase, state, reason, start, and finish timestamps.

---

## 4. Architectural Gap Analysis: Threading vs. Toolforge Jobs

| Dimension | In-Process Threading (`jobs_worker.py`) | Toolforge Jobs API (`toolforge_jobs_api_service.py`) | Migration Implication |
|---|---|---|---|
| **Process Isolation** | None (same Python runtime, shared heap). | Full (isolated container/pod in Kubernetes). | Eliminates web process crashes; requires externalized IPC. |
| **Authentication & Tokens** | Direct in-memory passing of user OAuth access tokens. | Cannot pass sensitive in-memory objects directly via CLI arguments. | Must securely persist or encrypt job run auth payloads, or read via secured temporary credential store/database. |
| **Parameters & Arguments** | Direct in-memory passing of Python dictionaries and objects. | Command line string (`cmd`) executed inside pod. | Job arguments must be stored in database or serialized to job-specific JSON config files on shared storage. |
| **Output & Progress** | Worker writes directly to JSON result files in NFS storage. | Pod writes to NFS and standard container `stdout`/`stderr`. | Results files continue on NFS; pod logs can additionally be inspected via `get_logs()`. |
| **Cancellation** | `threading.Event`, `.cancelled` flag file, DB polling. | `DELETE /jobs/v1/tool/{tool}/jobs/{id}`, plus DB polling and `.cancelled` flag file. | `delete_job` deletes Kubernetes Pod immediately; graceful stop can still use DB/file flags before forced kill. |
| **Monitoring & Polling** | Status updated directly by worker into database. | Pod runs independently. Web tier must poll or worker updates DB via its own database connection. | CLI worker running inside pod connects to DB to update status; Web app can also query Toolforge API for pod liveness. |
| **Local Development** | Out-of-the-box support without external dependencies. | Requires Toolforge Kubernetes cluster and API gateway client certificates. | System must support a dual-backend driver pattern (Local Threading/Subprocess vs. Cloud Toolforge). |

---

## 5. Detailed Technical Design for the Migration

### 5.1 Architecture Overview
The modernized architecture introduces an **Execution Backend Driver Pattern**:

```
+-------------------------------------------------------------------------+
|                               Flask Web Tier                            |
|                                                                         |
|   [StartJobView]  --> [JobExecutionService]                            |
|                              |                                          |
|               +--------------+--------------+                           |
|               |                             |                           |
|      (Toolforge Env)                  (Local Dev Env)                   |
|               v                             v                           |
|    [ToolforgeJobBackend]          [ThreadingJobBackend]                 |
|               |                             |                           |
|               v                             v                           |
|   Toolforge Jobs REST API           In-Process Thread                   |
|    (POST /jobs/v1/.../jobs)         (_runner daemon)                    |
+---------------+-----------------------------+---------------------------+
                |
                v  (Kubernetes Pod Scheduled)
+-------------------------------------------------------------------------+
|                     Toolforge Kubernetes Worker Pod                     |
|                                                                         |
|   Command: python -m src.app1 run-job --job-id 42                       |
|   - Loads Job Record #42 from Database                                  |
|   - Initializes Worker Class (BaseObjectsJobWorker)                     |
|   - Executes process(), updates DB and writes result JSON               |
+-------------------------------------------------------------------------+
```

### 5.2 Unified CLI Job Execution Engine
Currently, `cli_jobs.py` contains a rudimentary stub:
```python
@app.cli.command("run-job")
@click.argument("job_type")
@click.option("--update-all", is_flag=True)
def _run_job(job_type: str, update_all: bool): ...
```

To support executing specific scheduled jobs on Toolforge, the CLI must be enhanced to accept a specific database job ID:
```bash
python -m src.app1 run-job --job-id <JOB_ID>
```

#### CLI Execution Flow:
1. Pod launches with command:
   `python3 -m src.app1 run-job --job-id 42` (or via a wrapper shell script `run_job.sh 42`).
2. Flask CLI initializes application context and connects to the database.
3. Retrieves `JobRecord` with `id=42`.
4. Retrieves job configurations, stored argument payload, and serialized authentication payload from the job record or an encrypted temporary parameters record.
5. Instantiates the registered worker class for `job_record.job_type`.
6. Executes `worker.run()`.
7. `worker.run()` updates the database record status directly (`running` -> `completed` / `failed`) and saves JSON progress to `/data/project/<tool>/public_jobs/`.

### 5.3 Secure Argument and Credential Passing
Because `cmd` in Toolforge Jobs is visible via `list_jobs()` and Kubernetes process inspect tools, **sensitive credentials (like OAuth consumer tokens and user tokens) must never be passed in clear text on the command line**.

#### Solution:
1. Extend `JobRecord` (or create a paired `JobRunData` / `JobExecutionPayload` table/file):
   - Store non-sensitive job parameters as JSON in the database (`job_args`).
   - Store user authentication credentials securely (encrypted using the existing `OAUTH_ENCRYPTION_KEY` cipher) or in a restricted permission temporary file in `~/.jobs_auth/job_<id>.json` (chmod 600) readable only by the tool user.
2. The CLI worker loads credentials at runtime, executes the MediaWiki API tasks, and securely removes temporary credential files upon termination.

### 5.4 Toolforge Job Naming Convention
Toolforge job names must conform to regex `^[a-z0-9]([-a-z0-9]*[a-z0-9])?([.][a-z0-9]([-a-z0-9]*[a-z0-9])?)*$` with a max length of 52 characters.

**Standardized Naming Schema**:
```
mdw-{job_type_short}-{job_id}
```
*Example*: `mdw-fixref-104` or `mdw-allpages-42`.
This ensures uniqueness, easy correlation with database `id`, and complies with Kubernetes and Toolforge RFC naming constraints.

### 5.5 How to Start Jobs via Toolforge API
When a user clicks "Start Job" on the frontend:
1. `JobExecutionService.submit_job(job_type, user_auth, form_args)`:
   - Persists `JobRecord` in database (status `pending`).
   - Persists encrypted credentials/parameters for the job run.
   - Generates Toolforge job name: `f"mdw-{job_type[:20].replace('_', '-')}-{job_id}"`.
   - Constructs `NewJob` payload:
     ```python
     new_job: NewJob = {
         "name": job_name,
         "imagename": "python3.13",
         "cmd": f"/data/project/mdwiki/bin/run_job.sh {job_id}",
         "job_type": "one-off",
         "memory": job_data.memory or "1Gi",
         "cpu": job_data.cpu or "0.5",
         "emails": "none",
         "mount": "all",
         "retry": 0,
         "filelog": True,
         "filelog_stdout": f"/data/project/mdwiki/logs/job-{job_id}.out",
         "filelog_stderr": f"/data/project/mdwiki/logs/job-{job_id}.err",
     }
     ```
   - Calls `ToolforgeJobsService.create_job(new_job)`.
   - Updates `JobRecord` with `toolforge_job_name = job_name`.
   - Returns `job_id` to web controller for immediate redirect to job details page.

### 5.6 How to Query and Monitor Job Status
Job status monitoring operates via two coordinated mechanisms:

#### 1. Internal Worker Status Reporting (Push)
- As before, the worker class (`BaseObjectsJobWorker`) updates the MySQL database status (`running`, `completed`, `failed`) and updates the progress JSON file in shared storage.

#### 2. Toolforge Kubernetes Liveness Synchronization (Reconciliation / Pull)
- When the user visits the Job Details page or the Jobs List page:
  ```python
  def sync_job_status(job: JobRecord) -> None:
      if job.status in ("completed", "failed", "cancelled"):
          return  # Terminal state reached

      tf_job = toolforge_jobs_service.show_job(job.toolforge_job_name).get("job")
      if not tf_job:
          # Pod has completed and was cleaned up, or never scheduled
          return

      status_info = tf_job.get("status", {})
      short_status = status_info.get("short")  # pending, running, succeeded, failed

      if short_status == "succeeded" and job.status != "completed":
          job_service.update_job_status(job.id, "completed")
      elif short_status == "failed" and job.status != "failed":
          error_msgs = status_info.get("messages", [])
          job_service.update_job_status(job.id, "failed")
  ```
- **Crash Detection**: If a container pod is killed due to OOM (`exitcode 137`) or node eviction, the worker process will not have had the opportunity to run `after_run()`. The Toolforge status inspection immediately catches this discrepancy and transitions the database record from `running` to `failed`, preventing "ghost" running jobs.

### 5.7 How to Cancel and Stop Jobs
Cancellation operates in two stages:
1. **Graceful Cancellation**:
   - Write `.cancelled` flag file and mark DB record `cancelled` via `JobsService().cancel_job_db(job_id)`.
   - The CLI worker checking `is_cancelled()` gracefully halts at the next iteration, saves partial progress, and exits with code 0.
2. **Immediate / Forceful Pod Termination**:
   - Call `ToolforgeJobsService.delete_job(job.toolforge_job_name)`.
   - Kubernetes sends `SIGTERM` followed by `SIGKILL` to the pod, terminating it immediately.
   - The status syncer marks the database record as `cancelled`.

### 5.8 Log Retrieval & Inspection
- **Current**: The web UI reads result summary JSON files (`DrawResultFileView`).
- **Toolforge Enhanced**: The web UI can now display live container logs:
  - Using `ToolforgeJobsService.get_logs(job.toolforge_job_name)` to show raw execution trace directly in an admin/user log viewer tab.
  - Persistent fallback: Reading `/data/project/mdwiki/logs/job-{job_id}.out` and `.err` directly from shared NFS storage if the pod has already terminated and expired from Kubernetes pod cache.

---

## 6. Phased Migration Roadmap

```
+-----------------------------------------------------------------------------------+
| Phase 1: CLI Runner & Payload Persistence Foundation                              |
| - Implement `flask run-job --job-id <id>`                                         |
| - Implement secure job credential & parameter persistence                         |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 2: Execution Backend Abstraction Layer                                      |
| - Create `JobBackendInterface`, `ThreadingBackend`, `ToolforgeBackend`            |
| - Environment-driven factory: Auto-detect Toolforge vs. Local Dev                 |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 3: Toolforge Jobs Lifecycle Integration                                     |
| - Connect `start_job_form` to `ToolforgeJobBackend.submit()`                      |
| - Connect `cancel_job_worker` to `ToolforgeJobBackend.cancel()`                   |
| - Add status reconciliation check on job detail view                              |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 4: UI, Log Viewer & Admin Dashboard Enhancements                           |
| - Embed container log tab using `ToolforgeJobsService.get_logs()`                 |
| - Add Toolforge quota / capacity indicators to Admin Panel                        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 5: Verification, Staging & Full Production Cutover                          |
| - Validate zero regressions across local pytest test suite                        |
| - Deploy wrapper scripts to Toolforge NFS                                         |
| - Canary test on one-off job type before general rollout                          |
+-----------------------------------------------------------------------------------+
```

### Phase 1: CLI Runner & Payload Persistence Foundation
- **Goal**: Make any registered background job runnable in isolation via CLI using only its `job_id`.
- **Tasks**:
  1. Add `job_args` JSON column to `JobRecord` (or temporary JSON configuration file in secure directory).
  2. Implement `src/main_app/jobs_workers/cli_jobs.py` command:
     `flask --app src.app1 run-job --job-id <ID>`.
  3. Load job record, reconstitute user site / auth payload, instantiate worker class, and execute `worker.run()`.
  4. Test locally by running a test job end-to-end via CLI in bash.

### Phase 2: Execution Backend Abstraction Layer
- **Goal**: Allow transparent switching between threading (local) and Toolforge Jobs (production) without touching route controllers.
- **Tasks**:
  1. Create `src/main_app/jobs_workers/backends/`:
     - `base.py`: Defines `JobExecutionBackend` abstract interface (`submit(job_id, ...)`, `cancel(job_id, ...)`, `get_status(job_id)`).
     - `threading_backend.py`: Extracts current threading logic from `jobs_worker.py`.
     - `toolforge_backend.py`: Implements job submission and cancellation via `ToolforgeJobsService`.
     - `factory.py`: Returns backend based on configuration `JOB_BACKEND_DRIVER="toolforge" | "threading"`. Default to `threading` if Toolforge API credentials/certs are not present.

### Phase 3: Toolforge Jobs Lifecycle Integration
- **Goal**: Run background jobs as Toolforge one-off jobs in production.
- **Tasks**:
  1. Refactor `src/main_app/jobs_workers/jobs_worker.py`:
     - Redirect `_start_job_impl` to `get_job_backend().submit(...)`.
     - Redirect `cancel_job_worker` to `get_job_backend().cancel(...)`.
  2. Implement reconciliation helper in `JobsService` to detect died/OOM-killed pods via `ToolforgeJobsService.show_job()`.

### Phase 4: UI, Log Viewer & Admin Dashboard Enhancements
- **Goal**: Leverage Toolforge API capabilities in the UI.
- **Tasks**:
  1. Add "Live Pod Logs" tab to `src/templates/jobs_templates/base_details_public.html` calling the existing `ToolforgeJobsService.get_logs()`.
  2. Display Toolforge quota limits on the Admin dashboard (`/admin/tf_jobs/quotas`).

### Phase 5: Verification, Staging & Full Production Cutover
- **Goal**: Safe rollout without downtime or interrupted jobs.
- **Tasks**:
  1. Run comprehensive test suite (`pytest`) verifying that existing test fixtures continue to function seamlessly with the `threading` backend.
  2. Deploy wrapper shell script `run_job.sh` on Toolforge:
     ```bash
     #!/usr/bin/env bash
     set -e
     source /data/project/mdwiki/www/python/venv/bin/activate
     exec python -m src.app1 run-job --job-id "$1"
     ```
  3. Set `JOB_BACKEND_DRIVER=toolforge` in production environment.
  4. Perform canary verification with a safe, lightweight job (e.g., `find_and_replace` on a test wiki page).

---

## 7. Inventory of Code Modifications

### 7.1 Existing Files to Modify
1. **`src/main_app/jobs_workers/jobs_worker.py`**:
   - Refactor dispatching to delegate to `JobBackendFactory.get_backend()`.
   - Retain threading logic inside a dedicated `ThreadingJobBackend` class for backward compatibility and test environments.
2. **`src/main_app/jobs_workers/cli_jobs.py`**:
   - Add `--job-id` parameter to `run-job` command.
   - Add argument loading and execution lifecycle orchestration.
3. **`src/main_app/database/models.py`**:
   - Add `toolforge_job_name` (String, nullable) and `job_args` (Text/JSON, nullable) to `JobRecord`.
4. **`src/main_app/database/services/jobs_service.py`**:
   - Add helper methods to query and update Toolforge-specific fields (`set_toolforge_job_name`, `get_by_toolforge_name`).
5. **`src/main_app/public/shared_jobs_routes.py`**:
   - Add status sync hook when loading job detail view to update state if pod terminated unexpectedly.
6. **`src/main_app/config/settings.py`**:
   - Add configuration flags: `JOB_BACKEND_DRIVER` (`"threading"` or `"toolforge"`), `TOOLFORGE_JOB_IMAGE` (default `"python3.13"`), `TOOLFORGE_JOB_DEFAULT_MEMORY` (default `"1Gi"`).

### 7.2 New Files to Create
1. **`src/main_app/jobs_workers/backends/__init__.py`**:
   - Module exports for execution backends.
2. **`src/main_app/jobs_workers/backends/base.py`**:
   - Abstract base class defining `JobExecutionBackend`.
3. **`src/main_app/jobs_workers/backends/threading_backend.py`**:
   - Encapsulated threading executor for local development.
4. **`src/main_app/jobs_workers/backends/toolforge_backend.py`**:
   - Toolforge Jobs API executor interacting with `ToolforgeJobsService`.
5. **`src/main_app/jobs_workers/backends/factory.py`**:
   - Factory function selecting backend based on environment and availability of Toolforge certificates.
6. **`scripts/run_job.sh`**:
   - Toolforge executable entrypoint script for Kubernetes pods.
7. **`tests/unit/jobs_workers/test_toolforge_backend.py`**:
   - Unit tests mocking `ToolforgeJobsService` to verify job creation, parameter serialization, and cancellation.

---

## 8. Summary of Recommendations & Next Actions

1. **Adopt Driver Abstraction First**: Do not immediately delete threading code. The dual-backend approach (`threading` for local development & automated test suites, `toolforge` for production) prevents breaking local contributor workflows.
2. **Standardize Pod Entry Point**: Ensure all background job logic remains inside `BaseObjectsJobWorker` subclasses. Only the execution trigger changes (from `thread.start()` to `toolforge.create_job()`).
3. **Enforce Least Privilege & Secret Safety**: Never expose OAuth credentials or session cookies on CLI parameters. Rely on encrypted database records or ephemeral chmod 600 files.
4. **Leverage Native Toolforge Logs**: Replace custom ad-hoc logging with Toolforge's native container log capture (`toolforge.get_logs(...)`) to simplify debugging and monitoring.
