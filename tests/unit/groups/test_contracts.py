"""Structural contract shared by every GroupParser implementation."""

import pytest

from metar_taf_parser.groups.base import GroupParser
from metar_taf_parser.groups.clouds import CloudParser
from metar_taf_parser.groups.pressure import PressureParser
from metar_taf_parser.groups.temperature import TemperatureParser
from metar_taf_parser.groups.vertical_visibility import VerticalVisibilityParser
from metar_taf_parser.groups.visibility import VisibilityParser
from metar_taf_parser.groups.weather_phenomenon import WeatherPhenomenonParser
from metar_taf_parser.groups.wind import WindParser

ALL_GROUP_PARSERS = [
    WindParser,
    VisibilityParser,
    CloudParser,
    VerticalVisibilityParser,
    TemperatureParser,
    PressureParser,
    WeatherPhenomenonParser,
]


@pytest.mark.parametrize("parser_cls", ALL_GROUP_PARSERS)
class TestGroupParserContract:
    """Todo GroupParser must implement the protocol without altering its logic."""

    def test_satisfies_group_parser_protocol(self, parser_cls):
        """The class implements `matches()` and `parse()` with the correct signature."""
        assert isinstance(parser_cls(), GroupParser)
