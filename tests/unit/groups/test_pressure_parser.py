# tests/unit/groups/test_pressure_parser.py
"""Behavioral tests for `PressureParser` — the QNH/altimeter METAR/TAF group.

Grammar covered:
- Hectopascals (`Q` + 4 digits), read directly as whole hPa, e.g. `Q1015` -> 1015.0.
- Inches of mercury (`A` + 4 digits), read as hundredths of an inHg,
  e.g. `A2992` -> 29.92.

Each class below isolates one piece of the grammar so a single failing rule
doesn't hide behind unrelated ones.
"""

import pytest

from metar_taf_parser.enums import PressureUnit
from metar_taf_parser.groups.pressure import PressureParser
from metar_taf_parser.models import Pressure


@pytest.fixture
def parser():
    """Provides a fresh instance of PressureParser for each test."""
    return PressureParser()


class TestPressureParserMatches:
    """`matches()` should accept valid pressure tokens and reject all others."""

    VALID_TOKENS = [
        "Q1015",
        "Q0995",
        "A2992",
        "A3000",
    ]

    NON_PRESSURE_TOKENS = [
        "24010KT",  # wind
        "9999",  # visibility
        "FEW020",  # cloud layer
        "VV003",  # vertical visibility
        "18/12",  # temperature/dew point
        "CAVOK",
        "LEMD",  # station id
        "Q101",  # only 3 digits
        "Q10155",  # 5 digits
        "A299",  # only 3 digits
        "B1015",  # unknown unit prefix
        "QABCD",  # non-numeric
        "",
    ]

    @pytest.mark.parametrize("token", VALID_TOKENS)
    def test_accepts_valid_pressure_tokens(self, parser, token):
        """Tokens matching `Q`/`A` + exactly 4 digits should match."""
        assert parser.matches(token) is True

    @pytest.mark.parametrize("token", NON_PRESSURE_TOKENS)
    def test_rejects_non_pressure_tokens(self, parser, token):
        """Tokens from other groups, or malformed pressure tokens, should not match."""
        assert parser.matches(token) is False


class TestPressureParserParsesHectopascals:
    """`Q` prefix: whole hectopascals, read directly from the 4 digits."""

    CASES = [
        ("Q1015", Pressure(value=1015.0, unit=PressureUnit.HPA)),
        ("Q0995", Pressure(value=995.0, unit=PressureUnit.HPA)),
        ("Q0980", Pressure(value=980.0, unit=PressureUnit.HPA)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_hectopascals(self, parser, token, expected):
        """The 4 digits after `Q` map directly to `value` in `PressureUnit.HPA`."""
        assert parser.parse(token) == expected


class TestPressureParserParsesInchesOfMercury:
    """`A` prefix: inches of mercury, the 4 digits are hundredths of an inch."""

    CASES = [
        ("A2992", Pressure(value=29.92, unit=PressureUnit.INHG)),
        ("A3000", Pressure(value=30.0, unit=PressureUnit.INHG)),
        ("A2900", Pressure(value=29.0, unit=PressureUnit.INHG)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_inches_of_mercury(self, parser, token, expected):
        """The 4 digits after `A` are divided by 100 to get `value` in `PressureUnit.INHG`."""
        assert parser.parse(token) == expected
