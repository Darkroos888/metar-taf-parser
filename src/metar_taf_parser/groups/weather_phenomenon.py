"""Parser for present-weather METAR/TAF groups."""

from metar_taf_parser.models import PresentWeather


class WeatherPhenomenonParser:
    """Parses weather tokens (e.g. +TSRA, -SHSN) into a PresentWeather value object."""

    def matches(self, token: str) -> bool:
        """Return True if the token matches a present-weather group pattern. Logic pending."""
        raise NotImplementedError

    def parse(self, token: str) -> PresentWeather:
        """Parse a weather token into a PresentWeather instance. Logic pending."""
        raise NotImplementedError
