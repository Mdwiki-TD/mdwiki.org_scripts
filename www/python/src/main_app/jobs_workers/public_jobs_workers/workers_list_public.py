from ..objects import JobData
from .add_r_column.worker import AddRColumnWorker
from .add_rtt_template.worker import AddRttTemplateWorker
from .add_unlinkedwikibase.worker import AddUnlinkedWikibaseWorker
from .archive_today.worker import ArchiveTodayWorker
from .create_redirects.worker import CreateRedirectsWorker
from .duplicate_redirect.worker import DuplicateRedirectWorker
from .find_and_replace.worker import FindAndReplaceWorker
from .fix_cs1.worker import FixCs1Worker
from .fix_cs1_params.worker import FixCs1ParamsWorker
from .fixred_all.worker import FixRedAllWorker
from .fixref.worker import FixRefWorker
from .import_history.worker import ImportHistoryWorker
from .medicine_articles.worker import MedicineArticlesWorker
from .newupdater_all.worker import NewUpdaterAllWorker
from .owidpopup_all.worker import OwidPopupAllWorker
from .webarchive_remover.worker import WebarchiveRemoverWorker

jobs_data_for_all_pages: dict[str, JobData] = {
    "archive_today": JobData(
        job_type=ArchiveTodayWorker.JOB_TYPE,
        job_name="Remove archive.today links",
        job_list_template="jobs_templates/public/archive_today/list.html",
        job_class=ArchiveTodayWorker,
        job_args=[],
        start_confirm_message="Start removing archive.today links from all pages?",
        ready=True,
        description="",
    ),
    "newupdater_all": JobData(
        job_type=NewUpdaterAllWorker.JOB_TYPE,
        job_name="Medical content updater (Category:RTT)",
        job_list_template="jobs_templates/public/newupdater_all/list.html",
        job_class=NewUpdaterAllWorker,
        job_args=[],
        start_confirm_message="Start medical content updater for all `Category:RTT` pages?",
        ready=True,
        description="",
    ),
    "add_unlinkedwikibase": JobData(
        job_type=AddUnlinkedWikibaseWorker.JOB_TYPE,
        job_name="Add unlinkedwikibase tag",
        job_list_template="jobs_templates/public/add_unlinkedwikibase/list.html",
        job_class=AddUnlinkedWikibaseWorker,
        job_args=[],
        start_confirm_message="Start adding unlinkedwikibase tags to all pages?",
        description="",
    ),
    "fixred_all": JobData(
        job_type=FixRedAllWorker.JOB_TYPE,
        job_name="Fix Redirects in All Pages",
        job_list_template="jobs_templates/public/fixred_all/list.html",
        job_class=FixRedAllWorker,
        job_args=[],
        start_confirm_message="Start fixing redirects in all pages?",
        ready=True,
        description="",
    ),
    "fixref": JobData(
        job_type=FixRefWorker.JOB_TYPE,
        job_name="Normalize References",
        job_list_template="jobs_templates/public/fixref/list.html",
        job_class=FixRefWorker,
        job_args=[],
        start_confirm_message="",
        description="",
    ),
    "duplicate_redirect": JobData(
        job_type=DuplicateRedirectWorker.JOB_TYPE,
        job_name="Fix Duplicate Redirects",
        job_details_template="jobs_templates/public/duplicate_redirect/details.html",
        job_list_template="jobs_templates/public/duplicate_redirect/list.html",
        job_class=DuplicateRedirectWorker,
        job_args=[],
        start_confirm_message="Start fixing duplicate redirects?",
        ready=True,
        description="",
    ),
    "find_and_replace": JobData(
        job_type=FindAndReplaceWorker.JOB_TYPE,
        job_name="Find and Replace",
        job_list_template="jobs_templates/public/find_and_replace/list.html",
        job_class=FindAndReplaceWorker,
        job_args=[],
        start_confirm_message="",
        ready=True,
        description="",
    ),
    "add_rtt_template": JobData(
        job_type=AddRttTemplateWorker.JOB_TYPE,
        job_name="Add RTT Template",
        job_list_template="jobs_templates/public/add_rtt_template/list.html",
        job_class=AddRttTemplateWorker,
        job_args=[],
        start_confirm_message="Start adding RTT template to all Category:RTT pages?",
        description="",
    ),
    "fix_cs1_params": JobData(
        job_type=FixCs1ParamsWorker.JOB_TYPE,
        job_name="Fix reference parameters (Category:CS1 errors: redundant parameter)",
        job_list_template="jobs_templates/public/fix_cs1_params/list.html",
        job_class=FixCs1ParamsWorker,
        job_args=[],
        start_confirm_message="Start task for `Category:CS1 errors: redundant parameter` pages?",
        ready=True,
        description="",
    ),
    "fix_cs1": JobData(
        job_type=FixCs1Worker.JOB_TYPE,
        job_name="Fix missing periodical (Category:CS1 errors: missing periodical)",
        job_list_template="jobs_templates/public/fix_cs1/list.html",
        job_class=FixCs1Worker,
        job_args=[],
        start_confirm_message="Start task for `Category:CS1 errors: missing periodical` pages?",
        ready=True,
        description="",
    ),
    "owidpopup_all": JobData(
        job_type=OwidPopupAllWorker.JOB_TYPE,
        job_name="Replace {{OWIDPopup by {{OWID",
        job_list_template="jobs_templates/public/owidpopup_all/list.html",
        job_class=OwidPopupAllWorker,
        job_args=[],
        start_confirm_message="Start task for `Category:Gadget:OWIDPopup` pages?",
        ready=True,
        description="",
    ),
    "webarchive_remover": JobData(
        job_type=WebarchiveRemoverWorker.JOB_TYPE,
        job_name="Remove duplicate {{Webarchive}}",
        job_list_template="jobs_templates/public/webarchive_remover/list.html",
        job_class=WebarchiveRemoverWorker,
        job_args=[],
        start_confirm_message="Start removing duplicate {{Webarchive}} templates?",
        ready=True,
        description="",
    ),
}

jobs_data_one_page = {
    "add_r_column": JobData(
        job_type=AddRColumnWorker.JOB_TYPE,
        job_name="Add R column",
        job_details_template="one_page_templates/add_r_column/details.html",
        job_list_template="one_page_templates/add_r_column/list.html",
        job_class=AddRColumnWorker,
        job_args=[],
        start_confirm_message="",
        ready=True,
        description="",
    ),
    "import_history": JobData(
        job_type=ImportHistoryWorker.JOB_TYPE,
        job_name="Import History from Enwiki",
        job_details_template="jobs_templates/public/import_history/details.html",
        job_list_template="jobs_templates/public/import_history/list.html",
        job_class=ImportHistoryWorker,
        job_args=[],
        start_confirm_message="",
        description="",
    ),
    "create_redirects": JobData(
        job_type=CreateRedirectsWorker.JOB_TYPE,
        job_name="Copy Redirects from Enwiki",
        job_details_template="jobs_templates/public/create_redirects/details.html",
        job_list_template="jobs_templates/public/create_redirects/list.html",
        job_class=CreateRedirectsWorker,
        job_args=[],
        start_confirm_message="",
        description="",
    ),
    "medicine_articles": JobData(
        job_type=MedicineArticlesWorker.JOB_TYPE,
        job_name="Update Medicine Articles Stats",
        job_details_template="jobs_templates/public/medicine_articles/details.html",
        job_class=MedicineArticlesWorker,
        job_args=[],
        start_confirm_message="Start updating WikiProject Medicine article statistics?",
        ready=True,
        description="Generates a statistical report of medical articles by language for WikiProject Medicine and publishes it to mdwiki.org.",
    ),
}

jobs_data_public = jobs_data_for_all_pages | jobs_data_one_page

__all__ = [
    "jobs_data_for_all_pages",
    "jobs_data_one_page",
    "jobs_data_public",
]
