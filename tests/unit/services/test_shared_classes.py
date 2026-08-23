"""Unit tests for src/main_app/services/shared_classes.py module."""

from __future__ import annotations

from src.main_app.services.shared_classes import UpdaterTextOutcome


class TestUpdaterTextOutcome:
    def test_create_with_defaults(self):
        o = UpdaterTextOutcome(status="skipped")
        assert o.status == "skipped"
        assert o.old_text == ""
        assert o.new_text == ""
        assert o.newrevid == 0
        assert o.msg == ""

    def test_create_with_values(self):
        o = UpdaterTextOutcome(status="changes", old_text="old", new_text="new", newrevid=123, msg="done")
        assert o.old_text == "old"
        assert o.new_text == "new"
        assert o.newrevid == 123
        assert o.msg == "done"

    def test_to_json(self):
        o = UpdaterTextOutcome(status="saved", newrevid=456)
        d = o.to_json()
        assert d["status"] == "saved"
        assert d["newrevid"] == 456
        assert "old_text" in d
        assert "new_text" in d

    def test_all_kind_values(self):
        for status in ("notext", "changes", "saved"):
            o = UpdaterTextOutcome(status=status)
            assert o.status == status
