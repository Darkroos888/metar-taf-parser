# tests/unit/groups/test_temperature_parser.py
"""Behavioral tests for `TemperatureParser` — the temperature/dew point METAR group.

Grammar covered: `TT/DD`, two 2-digit fields separated by a slash — air
temperature and dew point, both in whole degrees Celsius. A field prefixed
with `M` is negative (e.g. `M05` -> -5). Air and dew point are independent,
so their signs can differ (e.g. `00/M02`).

Each class below isolates one piece of the grammar so a single failing rule
doesn't hide behind unrelated ones.
"""

import pytest

from metar_taf_parser.groups.temperature import TemperatureParser
from metar_taf_parser.models import Temperature


@pytest.fixture
def parser():
    """Provides a fresh instance of TemperatureParser for each test."""
    return TemperatureParser()


class TestTemperatureParserMatches:
    """`matches()` should accept valid temperature tokens and reject all others."""

    VALID_TOKENS = [
        "18/12",
        "M02/M05",
        "00/M02",
        "05/00",
        "00/00",
        "M00/M00",
        "20/",
    ]

    NON_TEMPERATURE_TOKENS = [
        "24010KT",  # wind
        "9999",  # visibility
        "FEW020",  # cloud layer
        "VV003",  # vertical visibility
        "Q1015",  # pressure
        "CAVOK",  # ceiling and visibility OK
        "AUTO",  # automated message
        "LEMD",  # station id
        "/12",  # missing air temperature
        "1812",  # missing slash
        "ABC/12",  # non-numeric air temperature
        "18/ABC",  # non-numeric dew point
        "180/120",  # 3 digits per field
        "M2/M5",  # single digit per field
        "",
    ]

    @pytest.mark.parametrize("token", VALID_TOKENS)
    def test_accepts_valid_temperature_tokens(self, parser, token):
        """Tokens matching `TT/DD` (each field optionally `M`-prefixed) should match."""
        assert parser.matches(token) is True

    @pytest.mark.parametrize("token", NON_TEMPERATURE_TOKENS)
    def test_rejects_non_temperature_tokens(self, parser, token):
        """Tokens from other groups, or malformed temperature tokens, should not match."""
        assert parser.matches(token) is False


class TestTemperatureParserParsesPositiveValues:
    """Both fields without the `M` prefix."""

    CASES = [
        ("18/12", Temperature(air=18, dew_point=12)),
        ("05/00", Temperature(air=5, dew_point=0)),
        ("00/00", Temperature(air=0, dew_point=0)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_positive_values(self, parser, token, expected):
        """Each field maps directly to its integer value in degrees Celsius."""
        assert parser.parse(token) == expected


class TestTemperatureParserParsesNegativeValues:
    """The `M` prefix negates a field."""

    CASES = [
        ("M02/M05", Temperature(air=-2, dew_point=-5)),
        ("00/M02", Temperature(air=0, dew_point=-2)),
        ("M03/00", Temperature(air=-3, dew_point=0)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_negative_values(self, parser, token, expected):
        """An `M`-prefixed field becomes negative; air and dew point signs are independent."""
        assert parser.parse(token) == expected


class TestTemperatureParserParsesNegativeZero:
    """Edge case: `M00` (temperature between 0.0 and -0.4°C, rounds to 0)."""

    def test_parses_negative_zero(self, parser):
        """`M00` parses to `0`, the only representable value for an int field."""
        assert parser.parse("M00/M00") == Temperature(air=0, dew_point=0)
