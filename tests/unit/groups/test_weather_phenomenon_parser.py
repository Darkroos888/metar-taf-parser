# tests/unit/groups/test_weather_phenomenon_parser.py
"""Behavioral tests for `WeatherPhenomenonParser` — the present-weather METAR/TAF group.

Grammar covered, in this fixed order:
- Optional intensity/proximity prefix: `-` (light), `+` (heavy), `VC` (in the
  vicinity). No prefix means moderate intensity.
- Optional descriptor (`SH`, `TS`, `FZ`, `DR`, `BL`, `BC`, `PR`, `MI`).
- Zero or more 2-letter phenomenon codes (`RA`, `SN`, `FG`, `BR`, ...), kept
  in the order they appear in the token (e.g. `RASN` -> RAIN, SNOW).

A token needs at least one descriptor or one phenomenon: `TS` (thunderstorm
without precipitation) and `VCSH` (showers in the vicinity) are valid with an
empty `phenomena` tuple, but a bare `-`, `+` or `VC` is not.

Out of scope: recent weather (`RE` prefix, part of the remarks-like trailing
groups) and `NSW` (no significant weather, TAF only) — both are rejected.

Each class below isolates one piece of the grammar so a single failing rule
doesn't hide behind unrelated ones.
"""

import pytest

from metar_taf_parser.enums import WeatherDescriptor, WeatherIntensity, WeatherPhenomenon
from metar_taf_parser.groups.weather_phenomenon import WeatherPhenomenonParser
from metar_taf_parser.models import PresentWeather


@pytest.fixture
def parser():
    """Provides a fresh instance of WeatherPhenomenonParser for each test."""
    return WeatherPhenomenonParser()


class TestWeatherPhenomenonParserMatches:
    """`matches()` should accept valid present-weather tokens and reject all others."""

    VALID_TOKENS = [
        "RA",
        "-RA",
        "+RA",
        "BR",
        "FG",
        "HZ",
        "-SHRA",
        "+TSRA",
        "-SHSN",
        "FZFG",
        "-FZDZ",
        "BCFG",
        "MIFG",
        "PRFG",
        "BLSN",
        "DRSN",
        "RASN",
        "-RASN",
        "+SHRASN",
        "TS",
        "VCTS",
        "VCSH",
        "VCFG",
        "+FC",
    ]

    NON_WEATHER_TOKENS = [
        "24010KT",  # wind
        "9999",  # visibility
        "FEW020",  # cloud layer
        "VV003",  # vertical visibility
        "18/12",  # temperature/dew point
        "Q1015",  # pressure
        "CAVOK",
        "LEMD",  # station id
        "AUTO",
        "COR",
        "SKC",
        "NSC",
        "NSW",  # no significant weather (out of scope)
        "RERA",  # recent weather (out of scope)
        "-",  # intensity without descriptor or phenomenon
        "+",
        "VC",
        "XX",  # unknown code
        "RAX",  # trailing garbage
        "XXRA",  # leading unknown code
        "+-RA",  # two intensity prefixes
        "RA+",  # intensity in the wrong position
        "",
    ]

    @pytest.mark.parametrize("token", VALID_TOKENS)
    def test_accepts_valid_weather_tokens(self, parser, token):
        """Intensity (optional) + descriptor (optional) + phenomena tokens match."""
        assert parser.matches(token) is True

    @pytest.mark.parametrize("token", NON_WEATHER_TOKENS)
    def test_rejects_non_weather_tokens(self, parser, token):
        """Tokens from other groups, or malformed weather tokens, should not match."""
        assert parser.matches(token) is False


class TestWeatherPhenomenonParserParsesIntensity:
    """Intensity/proximity prefix: `-`, none, `+`, `VC`."""

    CASES = [
        ("-RA", WeatherIntensity.LIGHT),
        ("RA", WeatherIntensity.MODERATE),
        ("+RA", WeatherIntensity.HEAVY),
        ("VCFG", WeatherIntensity.IN_VICINITY),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_intensity(self, parser, token, expected):
        """The prefix maps to the matching `WeatherIntensity`; no prefix is MODERATE."""
        assert parser.parse(token).intensity is expected


class TestWeatherPhenomenonParserParsesSinglePhenomenon:
    """Base case: one phenomenon, no descriptor."""

    CASES = [
        (
            "RA",
            PresentWeather(
                intensity=WeatherIntensity.MODERATE,
                phenomena=(WeatherPhenomenon.RAIN,),
            ),
        ),
        (
            "-DZ",
            PresentWeather(
                intensity=WeatherIntensity.LIGHT,
                phenomena=(WeatherPhenomenon.DRIZZLE,),
            ),
        ),
        (
            "BR",
            PresentWeather(
                intensity=WeatherIntensity.MODERATE,
                phenomena=(WeatherPhenomenon.MIST,),
            ),
        ),
        (
            "+FC",
            PresentWeather(
                intensity=WeatherIntensity.HEAVY,
                phenomena=(WeatherPhenomenon.FUNNEL_CLOUD,),
            ),
        ),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_single_phenomenon(self, parser, token, expected):
        """A single phenomenon code maps to a one-element `phenomena` tuple."""
        weather = parser.parse(token)
        assert weather == expected
        assert weather.descriptors == ()


class TestWeatherPhenomenonParserParsesDescriptor:
    """Optional descriptor before the phenomena."""

    CASES = [
        (
            "-SHRA",
            PresentWeather(
                intensity=WeatherIntensity.LIGHT,
                phenomena=(WeatherPhenomenon.RAIN,),
                descriptors=(WeatherDescriptor.SHOWERS,),
            ),
        ),
        (
            "+TSRA",
            PresentWeather(
                intensity=WeatherIntensity.HEAVY,
                phenomena=(WeatherPhenomenon.RAIN,),
                descriptors=(WeatherDescriptor.THUNDERSTORM,),
            ),
        ),
        (
            "FZFG",
            PresentWeather(
                intensity=WeatherIntensity.MODERATE,
                phenomena=(WeatherPhenomenon.FOG,),
                descriptors=(WeatherDescriptor.FREEZING,),
            ),
        ),
        (
            "BCFG",
            PresentWeather(
                intensity=WeatherIntensity.MODERATE,
                phenomena=(WeatherPhenomenon.FOG,),
                descriptors=(WeatherDescriptor.PATCHES,),
            ),
        ),
        (
            "BLSN",
            PresentWeather(
                intensity=WeatherIntensity.MODERATE,
                phenomena=(WeatherPhenomenon.SNOW,),
                descriptors=(WeatherDescriptor.BLOWING,),
            ),
        ),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_descriptor(self, parser, token, expected):
        """The descriptor maps to a one-element `descriptors` tuple."""
        assert parser.parse(token) == expected

    def test_descriptors_default_to_empty_when_absent(self, parser):
        """Without a descriptor in the token, `descriptors` is an empty tuple."""
        assert parser.parse("-RA").descriptors == ()


class TestWeatherPhenomenonParserParsesMultiplePhenomena:
    """Several phenomenon codes concatenated in one token."""

    CASES = [
        (
            "RASN",
            PresentWeather(
                intensity=WeatherIntensity.MODERATE,
                phenomena=(WeatherPhenomenon.RAIN, WeatherPhenomenon.SNOW),
            ),
        ),
        (
            "+SHRASN",
            PresentWeather(
                intensity=WeatherIntensity.HEAVY,
                phenomena=(WeatherPhenomenon.RAIN, WeatherPhenomenon.SNOW),
                descriptors=(WeatherDescriptor.SHOWERS,),
            ),
        ),
        (
            "-SNRA",
            PresentWeather(
                intensity=WeatherIntensity.LIGHT,
                phenomena=(WeatherPhenomenon.SNOW, WeatherPhenomenon.RAIN),
            ),
        ),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_multiple_phenomena_in_order(self, parser, token, expected):
        """Phenomena are kept in token order (the first one is the dominant one)."""
        assert parser.parse(token) == expected


class TestWeatherPhenomenonParserParsesDescriptorOnly:
    """Descriptor without phenomenon: `TS`, `VCTS`, `VCSH`."""

    CASES = [
        (
            "TS",
            PresentWeather(
                intensity=WeatherIntensity.MODERATE,
                phenomena=(),
                descriptors=(WeatherDescriptor.THUNDERSTORM,),
            ),
        ),
        (
            "VCTS",
            PresentWeather(
                intensity=WeatherIntensity.IN_VICINITY,
                phenomena=(),
                descriptors=(WeatherDescriptor.THUNDERSTORM,),
            ),
        ),
        (
            "VCSH",
            PresentWeather(
                intensity=WeatherIntensity.IN_VICINITY,
                phenomena=(),
                descriptors=(WeatherDescriptor.SHOWERS,),
            ),
        ),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_descriptor_only(self, parser, token, expected):
        """A bare descriptor parses with an empty `phenomena` tuple."""
        assert parser.parse(token) == expected
