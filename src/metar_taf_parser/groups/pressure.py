"""Parser for the pressure (QNH/altimeter) METAR/TAF group."""
import re
from metar_taf_parser.enums import PressureUnit
from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.models import Pressure



class PressureParser:
    """Parses pressure tokens (e.g. Q1015, A2992) into a Pressure value object."""

    _PATTERN = re.compile(
        r"(?P<unit>[QA])(?P<digits>\d{4})"
    )

    _DIVISORS = {PressureUnit.HPA: 1, PressureUnit.INHG: 100}

    def matches(self, token: str) -> bool:
        """Return True if the token matches the pressure group pattern. Logic pending."""
        return self._PATTERN.fullmatch(token) is not None

    def parse(self, token: str) -> Pressure:
        """Parse a pressure token into a Pressure instance. Logic pending."""
        match = self._PATTERN.fullmatch(token)
        if match is None:
            raise ParseError(f"not a vertical visibility group: {token!r}")
        unit = PressureUnit(match.group("unit"))
        return Pressure(value=int(match.group("digits"))/self._DIVISORS[unit], unit=unit)
