from unittest.mock import MagicMock

from src.main_app.app_routes.jobs_routes_utils import can_manage_job


class TestCanManageJob:
    def test_no_user(self):
        job = MagicMock()
        assert can_manage_job(job, None) is False

    def test_admin_user(self):
        job = MagicMock()
        job.username = "someone"
        user = MagicMock()
        user.username = "admin_user"
        user.is_active_admin = True
        assert can_manage_job(job, user) is True

    def test_job_owner(self):
        job = MagicMock()
        job.username = "owner"
        user = MagicMock()
        user.username = "owner"
        user.is_active_admin = False
        assert can_manage_job(job, user) is True

    def test_non_owner_non_admin(self):
        job = MagicMock()
        job.username = "someone_else"
        user = MagicMock()
        user.username = "regular_user"
        user.is_active_admin = False
        assert can_manage_job(job, user) is False

    def test_job_with_no_username(self):
        job = MagicMock()
        job.username = None
        user = MagicMock()
        user.username = "user"
        user.is_active_admin = False
        assert can_manage_job(job, user) is False
