""" """

from src.main_app.shared.new_updater.bots.Remove import portal_remove


def test_it():
    text = "{{portal bar|Medicine}}"

    new_text = portal_remove(text)

    expected = ""

    assert new_text == expected
