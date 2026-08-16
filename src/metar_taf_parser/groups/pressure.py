"""Parser for the pressure (QNH/altimeter) METAR/TAF group."""

from metar_taf_parser.models import Pressure


class PressureParser:
    """Parses pressure tokens (e.g. Q1015, A2992) into a Pressure value object."""

    def matches(self, token: str) -> bool:
        """Return True if the token matches the pressure group pattern. Logic pending."""
        raise NotImplementedError

    def parse(self, token: str) -> Pressure:
        """Parse a pressure token into a Pressure instance. Logic pending."""
        raise NotImplementedError
