"""Parser for the wind METAR/TAF group."""

import re

from metar_taf_parser.enums import WindUnit
from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.models import Wind, WindVariation


class WindParser:
    """Parses wind tokens (e.g. 24010G20KT, 210V270) into Wind or WindVariation objects."""

    # Two alternatives:
    #   wind group:  direction (3 digits or VRB) + speed (2-3 digits) + optional gust + unit
    #   range group: dddVddd, the variable direction range that follows a wind group
    _PATTERN = re.compile(
        r"(?P<direction>\d{3}|VRB)(?P<speed>\d{2,3})(?:G(?P<gust>\d{2,3}))?(?P<unit>KT|MPS|KMH)"
        r"|(?P<range_from>\d{3})V(?P<range_to>\d{3})"
    )

    def matches(self, token: str) -> bool:
        """Return True if the token is a wind group or a variable direction range."""
        return self._PATTERN.fullmatch(token) is not None

    def parse(self, token: str) -> Wind | WindVariation:
        """Parse a wind token.

        Returns:
            A `Wind` for a wind group (`24010G20KT`, `VRB03KT`), or a
            `WindVariation` for a range group (`210V270`), which the report
            parser folds into the preceding wind.

        Raises:
            ParseError: If the token is neither a wind nor a range group.
        """
        match = self._PATTERN.fullmatch(token)
        if match is None:
            raise ParseError(f"not a wind group: {token!r}")

        if match.group("range_from") is not None:
            return WindVariation(
                from_direction=int(match.group("range_from")),
                to_direction=int(match.group("range_to")),
            )

        direction = match.group("direction")
        gust = match.group("gust")
        return Wind(
            direction=None if direction == "VRB" else int(direction),
            speed=int(match.group("speed")),
            unit=WindUnit(match.group("unit")),
            gust=int(gust) if gust is not None else None,
            variable=direction == "VRB",
        )
