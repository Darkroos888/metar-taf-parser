# tests/unit/groups/test_vertical_visibility_parser.py
"""Behavioral tests for `VerticalVisibilityParser` — the `VVxxx` METAR/TAF group.

Grammar covered: `VV` followed by exactly 3 digits, the vertical visibility
in hundreds of feet (e.g. `VV003` -> 300 ft), or by `///` when the height
can't be measured (automated stations) -> `height_ft=None`. Reported when the sky is
obscured (fog, heavy precipitation) and no distinct cloud layers can be
identified — it's mutually exclusive with the cloud groups in the real
grammar (see CONTEXT.md's domain model notes on `SkyCondition`).

Each class below isolates one piece of the grammar so a single failing rule
doesn't hide behind unrelated ones.
"""

import pytest

from metar_taf_parser.groups.vertical_visibility import VerticalVisibilityParser
from metar_taf_parser.models import VerticalVisibility


@pytest.fixture
def parser():
    """Provides a fresh instance of VerticalVisibilityParser for each test."""
    return VerticalVisibilityParser()


class TestVerticalVisibilityParserMatches:
    """`matches()` should accept valid VVxxx tokens and reject all others."""

    VALID_TOKENS = [
        "VV003",
        "VV000",
        "VV020",
        "VV100",
        "VV///",
    ]

    NON_VERTICAL_VISIBILITY_TOKENS = [
        "9999",  # visibility
        "FEW020",  # cloud layer
        "OVC010",  # cloud layer (also starts with a two-letter code)
        "24010KT",  # wind
        "VRB03KT",  # wind, starts with V but not VV
        "Q1015",  # pressure
        "18/12",  # temperature/dew point
        "CAVOK",  # ceiling and visibility OK
        "AUTO",  # automated message
        "LEMD",  # station id
        "VV03",  # only 2 digits
        "VV0003",  # 4 digits
        "VVABC",  # non-numeric
        "VV",  # missing digits entirely
        "VV//",  # only 2 slashes
        "VV0//",  # digits and slashes mixed
        "",
    ]

    @pytest.mark.parametrize("token", VALID_TOKENS)
    def test_accepts_valid_vertical_visibility_tokens(self, parser, token):
        """Tokens matching `VV` + exactly 3 digits should match."""
        assert parser.matches(token) is True

    @pytest.mark.parametrize("token", NON_VERTICAL_VISIBILITY_TOKENS)
    def test_rejects_non_vertical_visibility_tokens(self, parser, token):
        """Tokens from other groups, or malformed VVxxx tokens, should not match."""
        assert parser.matches(token) is False


class TestVerticalVisibilityParserParsesHeight:
    """The 3-digit suffix should be read as hundreds of feet."""

    CASES = [
        ("VV003", VerticalVisibility(height_ft=300)),
        ("VV020", VerticalVisibility(height_ft=2000)),
        ("VV100", VerticalVisibility(height_ft=10000)),
        ("VV005", VerticalVisibility(height_ft=500)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_height(self, parser, token, expected):
        """The digits should be multiplied by 100 to get `height_ft`."""
        assert parser.parse(token) == expected


class TestVerticalVisibilityParserParsesZeroHeight:
    """Edge case: `VV000` (indefinite ceiling, vertical visibility down to the ground)."""

    def test_parses_zero_height(self, parser):
        """`VV000` should parse to `height_ft=0`, not be rejected or raise."""
        assert parser.parse("VV000") == VerticalVisibility(height_ft=0)


class TestVerticalVisibilityParserParsesUnknownHeight:
    """`VV///`: the sky is obscured but the height can't be measured."""

    def test_parses_unknown_height_as_none(self, parser):
        """`VV///` should parse to `height_ft=None`, not 0 and not an error."""
        assert parser.parse("VV///") == VerticalVisibility(height_ft=None)
