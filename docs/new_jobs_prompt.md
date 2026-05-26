write a plan to merge old jobs into new_jobs, while keeping old `jobs` as its for `refernces`

all jobs in `flask_app/main_app/jobs`

    -   create_redirects
    -   duplicate_redirect
    -   find_and_replace
    -   fixred_all
    -   fixref
    -   import_history

should use `flask_app/main_app/new_jobs/jobs_worker.py`

we have an example of new_jobs logic: `copy_svg_langs`

start by creating folder for each job in `flask_app/main_app/new_jobs/workers`: - `__init__.py` and `worker.py` - copy logic from `flask_app/main_app/new_jobs/workers/copy_svg_langs`
