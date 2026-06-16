from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class JobData:
    job_type: str
    job_name: str
    job_list_template: str

    job_callable: Callable
    job_args: list[dict[str, str]] = field(default_factory=list)
    start_confirm_message: str | None = None
    job_details_template: Optional[str] = "jobs_templates/_help_templates/shared_details.html"
    ready: bool = False


__all__ = [
    "JobData",
]
