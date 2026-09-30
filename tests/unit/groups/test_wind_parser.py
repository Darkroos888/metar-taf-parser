"""Behavioral tests for `WindParser` — the surface wind METAR group.

Grammar covered: direction, speed, gust, unit (`KT`/`MPS`/`KMH`), variable
direction (`VRB`), calm wind (`00000KT`) and the variable direction range
group (`dddVddd`, e.g. `100V180`).

The range group is its own token (`24010KT 210V270`), so `parse()` returns
it as a separate `WindVariation`; folding it into the preceding
`Wind.variable_range` is the report parser's job (`_assemble()`). A `Wind`
coming out of this parser therefore always has `variable_range=None`.

Each class below isolates one piece of the grammar so a single failing rule
doesn't hide behind unrelated ones.
"""

import pytest

from metar_taf_parser.enums import WindUnit
from metar_taf_parser.groups.wind import WindParser
from metar_taf_parser.models import Wind, WindVariation


@pytest.fixture
def parser():
    """Provides a fresh instance of WindParser for each test."""
    return WindParser()


class TestWindParserMatches:
    """`matches()` should accept valid wind tokens and reject all others."""

    VALID_TOKENS = [
        "24010KT",
        "24010G20KT",
        "00000KT",
        "VRB03KT",
        "VRB02G08KT",
        "27015MPS",
        "18008KMH",
        "12015G25KMH",
        "36099KT",
        "09005G12MPS",
        "100V180",  # wind may vary, so a group to indicate the oscillations is added
    ]

    NON_WIND_TOKENS = [
        "9999",  # visibility
        "2000NE",  # directional visibility
        "FEW020",  # cloud layer
        "VV003",  # vertical visibility
        "Q1015",  # pressure (hPa)
        "A2992",  # pressure (inHg)
        "18/12",  # temperature/dew point
        "M02/M08",  # temperature/dew point below zero
        "+TSRA",  # present weather
        "LEMD",  # station id
        "CAVOK",  # ceiling and visibility OK
        "161200Z",  # observation time
        "AUTO",  # report auto-provided
        "COR",  # correction
        "100V",  # second direction missing
        "V200",  # first direction missing
        "10V180",  # first direction with only 2 digits
        "100V1800",  # second direction with 4 digits
        "100V180KT",  # range group with a unit suffix
        "2401KT",  # direction/speed with only 2 digits
        "24010",  # missing unit
        "ABCDEKT",  # non-numeric direction/speed
        "24010GKT",  # G with no gust value
        "",
    ]

    @pytest.mark.parametrize("token", VALID_TOKENS)
    def test_accepts_valid_wind_tokens(self, parser, token):
        """Valid tokens matching dddffGffUU, VRB, or calm formats should match."""
        assert parser.matches(token) is True

    @pytest.mark.parametrize("token", NON_WIND_TOKENS)
    def test_rejects_non_wind_tokens(self, parser, token):
        """Tokens from other groups or invalid wind formats should not match."""
        assert parser.matches(token) is False


class TestWindParserParsesDirectionAndSpeed:
    """Base case: direction + speed, without gusts."""

    CASES = [
        ("24010KT", Wind(direction=240, speed=10, unit=WindUnit.KT)),
        ("09005KT", Wind(direction=90, speed=5, unit=WindUnit.KT)),
        ("36020KT", Wind(direction=360, speed=20, unit=WindUnit.KT)),
        ("01003KT", Wind(direction=10, speed=3, unit=WindUnit.KT)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_direction_and_speed(self, parser, token, expected):
        """Direction and speed should be correctly extracted without gust or variability."""
        wind = parser.parse(token)
        assert wind == expected
        assert wind.gust is None
        assert wind.variable is False
        assert wind.variable_range is None


class TestWindParserParsesGust:
    """Optional gust component (`Gff`)."""

    CASES = [
        ("24010G20KT", Wind(direction=240, speed=10, gust=20, unit=WindUnit.KT)),
        ("18025G35KT", Wind(direction=180, speed=25, gust=35, unit=WindUnit.KT)),
        ("09008G15MPS", Wind(direction=90, speed=8, gust=15, unit=WindUnit.MPS)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_gust(self, parser, token, expected):
        """When the token includes `Gff`, `gust` should reflect that value."""
        assert parser.parse(token) == expected

    def test_gust_defaults_to_none_when_absent(self, parser):
        """Without `Gff` in the token, `gust` should be None."""
        assert parser.parse("24010KT").gust is None


class TestWindParserParsesUnit:
    """Speed units: KT, MPS, KMH."""

    CASES = [
        ("24010KT", WindUnit.KT),
        ("24010MPS", WindUnit.MPS),
        ("24010KMH", WindUnit.KMH),
    ]

    @pytest.mark.parametrize("token, expected_unit", CASES)
    def test_parses_unit(self, parser, token, expected_unit):
        """The suffix unit in the token should map to the corresponding `WindUnit`."""
        assert parser.parse(token).unit == expected_unit


class TestWindParserParsesVariableDirection:
    """Single-token variable direction (`VRB`), without an associated range."""

    CASES = [
        ("VRB03KT", Wind(direction=None, speed=3, unit=WindUnit.KT, variable=True)),
        (
            "VRB02G08KT",
            Wind(direction=None, speed=2, gust=8, unit=WindUnit.KT, variable=True),
        ),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_variable_direction(self, parser, token, expected):
        """`VRB` should result in direction=None and variable=True."""
        wind = parser.parse(token)
        assert wind == expected
        assert wind.variable_range is None


class TestWindParserParsesCalmWind:
    """Calm wind (`00000KT`)."""

    def test_parses_calm_wind(self, parser):
        """Calm wind should set direction and speed to 0, without gust or variability."""
        wind = parser.parse("00000KT")
        assert wind == Wind(direction=0, speed=0, unit=WindUnit.KT)
        assert wind.gust is None
        assert wind.variable is False


class TestWindParserParsesVariationRange:
    """Variable direction range group (`dddVddd`), returned as a `WindVariation`."""

    CASES = [
        ("100V180", WindVariation(from_direction=100, to_direction=180)),
        ("210V270", WindVariation(from_direction=210, to_direction=270)),
        ("350V030", WindVariation(from_direction=350, to_direction=30)),  # crosses north
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_variation_range(self, parser, token, expected):
        """Both 3-digit directions are read in degrees, in token order."""
        assert parser.parse(token) == expected
