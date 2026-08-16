# tests/unit/groups/test_vertical_visibility_parser.py
"""Structural contract test for VerticalVisibilityParser."""

from metar_taf_parser.groups.base import GroupParser
from metar_taf_parser.groups.vertical_visibility import VerticalVisibilityParser


class TestVerticalVisibilityParserContract:
    """Verifies the class satisfies the GroupParser protocol, ignoring logic."""

    def test_satisfies_group_parser_protocol(self):
        """VerticalVisibilityParser must implement matches() and parse()."""
        parser = VerticalVisibilityParser()
        assert isinstance(parser, GroupParser)
