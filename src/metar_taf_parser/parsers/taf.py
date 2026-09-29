"""TAF report parser."""

from datetime import datetime

from metar_taf_parser.groups.clouds import CloudParser
from metar_taf_parser.groups.pressure import PressureParser
from metar_taf_parser.groups.temperature import TemperatureParser
from metar_taf_parser.groups.vertical_visibility import VerticalVisibilityParser
from metar_taf_parser.groups.visibility import VisibilityParser
from metar_taf_parser.groups.weather_phenomenon import WeatherPhenomenonParser
from metar_taf_parser.groups.wind import WindParser
from metar_taf_parser.models import Taf
from metar_taf_parser.parsers.base import AbstractReportParser


class TafParser(AbstractReportParser):
    """Parses a raw TAF report into a `Taf` value object."""

    def __init__(self) -> None:
        """Register the group parsers in dispatch order."""
        super().__init__(
            [
                WindParser(),
                VisibilityParser(),
                CloudParser(),
                VerticalVisibilityParser(),
                TemperatureParser(),
                PressureParser(),
                WeatherPhenomenonParser(),
            ]
        )

    def _assemble(self, raw: str, results: list[object], reference: datetime) -> Taf:
        """Build a `Taf` from the dispatched results. Logic pending."""
        raise NotImplementedError
