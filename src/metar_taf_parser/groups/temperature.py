"""Parser for the temperature/dew point METAR/TAF group."""

from metar_taf_parser.models import Temperature


class TemperatureParser:
    """Parses temperature tokens (e.g. 18/12, M02/M05) into a Temperature value object."""

    def matches(self, token: str) -> bool:
        """Return True if the token matches the temperature group pattern. Logic pending."""
        raise NotImplementedError

    def parse(self, token: str) -> Temperature:
        """Parse a temperature token into a Temperature instance. Logic pending."""
        raise NotImplementedError
