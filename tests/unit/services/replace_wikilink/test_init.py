

from src.main_app.services.replace_wikilink import replace_wikilink_destinations


class TestReplaceWikilinkDestinations:

    def test_replace_wikilink_destinations(self):
        text = """#REDIRECT [[Draft:T341027-1#zz]]\n\n{{Redirect category shell|\n{{R from move}}\n}}"""
        result = replace_wikilink_destinations(text, "Draft:T341027-1", "Draft:T341027-3")
        assert result == "#REDIRECT [[Draft:T341027-3#zz]]\n\n{{Redirect category shell|\n{{R from move}}\n}}"
