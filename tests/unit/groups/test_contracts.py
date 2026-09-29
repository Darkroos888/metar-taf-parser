"""Contract shared by every GroupParser implementation.

Besides the Protocol shape, every parser agrees on one error rule: `parse()`
on a token its own `matches()` rejects raises `ParseError` (or a subclass),
never a stray `AttributeError`/`ValueError` from the regex internals.
"""

import pytest

from metar_taf_parser.exceptions import ParseError
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

# Tokens no group parser accepts: empty, a station id, and plain garbage.
UNPARSEABLE_TOKENS = ["", "LEMD", "#@!"]


@pytest.mark.parametrize("parser_cls", ALL_GROUP_PARSERS)
class TestGroupParserContract:
    """Todo GroupParser must implement the protocol without altering its logic."""

    def test_satisfies_group_parser_protocol(self, parser_cls):
        """The class implements `matches()` and `parse()` with the correct signature."""
        assert isinstance(parser_cls(), GroupParser)

    @pytest.mark.parametrize("token", UNPARSEABLE_TOKENS)
    def test_parse_raises_parse_error_on_unmatched_token(self, parser_cls, token):
        """`parse()` on a token that doesn't match raises ParseError."""
        with pytest.raises(ParseError):
            parser_cls().parse(token)
