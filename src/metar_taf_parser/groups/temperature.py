"""Parser for the temperature/dew point METAR/TAF group."""

import re

from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.models import Temperature


class TemperatureParser:
    """Parses temperature tokens (e.g. 18/12, M02/M05) into a Temperature value object."""

    _PATTERN = re.compile(
        r"(?P<air>M?\d{2})/(?P<dew_point>(M?\d{2}))?"
    )

    def matches(self, token: str) -> bool:
        """Return True if the token matches the temperature group pattern."""
        return self._PATTERN.fullmatch(token) is not None

    def parse(self, token: str) -> Temperature:
        """Parse a temperature token into a Temperature instance."""
        match = self._PATTERN.fullmatch(token)
        if match is None:
            raise ParseError(f"not a temperature group: {token!r}")
        dew_point = match.group("dew_point")
        return Temperature(
            air = self._celsius(match.group("air")),
            dew_point = self._celsius(dew_point) if dew_point is not None else None
        )
    @staticmethod
    def _celsius(value: str) -> int:
        if value.startswith("M"):
            return -int(value[1:])
        return int(value)
