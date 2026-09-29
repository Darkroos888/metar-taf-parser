"""Parser for the vertical visibility (VVxxx) METAR/TAF group."""

import re

from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.models import VerticalVisibility


class VerticalVisibilityParser:
    """Parses VVxxx tokens into a VerticalVisibility value object."""

    _PATTERN = re.compile(r"VV(\d{3}|///)")

    def matches(self, token: str) -> bool:
        """Return True if the token matches the VVxxx pattern."""
        return self._PATTERN.fullmatch(token) is not None

    def parse(self, token: str) -> VerticalVisibility:
        """Parse a VVxxx token into a VerticalVisibility instance."""
        match = self._PATTERN.fullmatch(token)
        if match is None:
            raise ParseError(f"not a vertical visibility group: {token!r}")
        height = match.group(1)
        if height == "///":
            return VerticalVisibility(height_ft=None)
        return VerticalVisibility(height_ft=int(match.group(1)) * 100)
