```

def newupdater_all_worker_entry(data: JobsRunner) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {data.job_id}: newupdater_all")
    worker = NewUpdaterAllWorker(data)
    worker.run()


```

We dont need workers_entry functions.

replace all `job_callable` with `job_class`

example:

before:

```
    "newupdater_all": JobData(
        job_type="newupdater_all",
        job_name="Medical content updater (Category:RTT)",
        job_list_template="jobs_templates/public/newupdater_all/list.html",
        job_callable=newupdater_all_worker_entry,
        job_args=[],
        start_confirm_message="Start medical content updater for all Category:RTT pages?",
        ready=True,
    ),
```

after:

```
    "newupdater_all": JobData(
        job_type="newupdater_all",
        job_name="Medical content updater (Category:RTT)",
        job_list_template="jobs_templates/public/newupdater_all/list.html",
        job_class=NewUpdaterAllWorker,
        job_args=[],
        start_confirm_message="Start medical content updater for all Category:RTT pages?",
        ready=True,
    ),
```

---

update `<type>_jobs_workers/<job_type>/__init__.py`

example:

before:

```
from .worker import add_r_column_worker_entry

__all__ = [
    "add_r_column_worker_entry",
]

```

after:

```
from .worker import AddRColumnWorker

__all__ = [
    "AddRColumnWorker",
]
```
