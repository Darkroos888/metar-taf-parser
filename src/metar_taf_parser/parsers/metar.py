"""METAR report parser."""

import re
from dataclasses import dataclass, replace
from datetime import datetime

from metar_taf_parser.exceptions import InvalidReportError
from metar_taf_parser.groups.clouds import CloudParser
from metar_taf_parser.groups.pressure import PressureParser
from metar_taf_parser.groups.temperature import TemperatureParser
from metar_taf_parser.groups.vertical_visibility import VerticalVisibilityParser
from metar_taf_parser.groups.visibility import VisibilityParser
from metar_taf_parser.groups.weather_phenomenon import WeatherPhenomenonParser
from metar_taf_parser.groups.wind import WindParser
from metar_taf_parser.models import (
    CloudLayer,
    Metar,
    PresentWeather,
    Pressure,
    SkyCondition,
    Temperature,
    VerticalVisibility,
    Visibility,
    WeatherConditions,
    Wind,
    WindVariation,
)
from metar_taf_parser.parsers.base import AbstractReportParser


@dataclass(frozen=True)
class MetarHeader:
    """Header groups of a METAR: `[METAR|SPECI] [COR] station DDHHMMZ [AUTO] [COR]`.

    Internal intermediate between `_parse_header()` and `_assemble()`, not
    part of the public domain model.
    """

    station_id: str
    observation_time: datetime
    auto: bool = False
    corrected: bool = False


class MetarParser(AbstractReportParser):
    """Parses a raw METAR report into a `Metar` value object."""

    _REPORT_TYPES = frozenset({"METAR", "SPECI"})
    _AUTO = "AUTO"
    _CORRECTED = "COR"
    # ICAO location indicator: a letter followed by three letters or digits.
    _STATION_PATTERN = re.compile(r"[A-Z][A-Z0-9]{3}")
    _TIME_PATTERN = re.compile(r"(?P<day>\d{2})(?P<hour>\d{2})(?P<minute>\d{2})Z")

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

    def _parse_header(
        self, tokens: list[str], reference: datetime
    ) -> tuple[MetarHeader, list[str]]:
        """Consume the METAR header and return it with the body tokens.

        Reads `[METAR|SPECI] [COR] station DDHHMMZ`, then any `AUTO`/`COR`
        that follow the timestamp.

        Raises:
            InvalidReportError: If the station id or the timestamp is missing
                or invalid.
        """
        index = 0
        corrected = False

        if index < len(tokens) and tokens[index] in self._REPORT_TYPES:
            index += 1
        if index < len(tokens) and tokens[index] == self._CORRECTED:
            corrected = True
            index += 1

        if index >= len(tokens) or not self._STATION_PATTERN.fullmatch(tokens[index]):
            raise InvalidReportError("missing or invalid station id")
        station_id = tokens[index]
        index += 1

        time_match = self._TIME_PATTERN.fullmatch(tokens[index]) if index < len(tokens) else None
        if time_match is None:
            raise InvalidReportError("missing or invalid observation time (DDHHMMZ)")
        observation_time = self._complete_timestamp(
            int(time_match.group("day")),
            int(time_match.group("hour")),
            int(time_match.group("minute")),
            reference,
        )
        index += 1

        auto = False
        while index < len(tokens) and tokens[index] in (self._AUTO, self._CORRECTED):
            if tokens[index] == self._AUTO:
                auto = True
            else:
                corrected = True
            index += 1

        header = MetarHeader(
            station_id=station_id,
            observation_time=observation_time,
            auto=auto,
            corrected=corrected,
        )
        return header, tokens[index:]

    def _assemble(
        self, raw: str, header: MetarHeader, results: list[object], reference: datetime
    ) -> Metar:
        """Build a `Metar` from the header and the dispatched results.

        Cloud layers and vertical visibility are gathered into one
        `SkyCondition`; a `WindVariation` is folded into the preceding wind.

        Raises:
            InvalidReportError: If wind, temperature or pressure is missing,
                or a wind variation has no wind group before it.
        """
        wind: Wind | None = None
        visibility: Visibility | None = None
        clouds: list[CloudLayer] = []
        vertical_visibility: VerticalVisibility | None = None
        weather: list[PresentWeather] = []
        temperature: Temperature | None = None
        pressure: Pressure | None = None
        cavok = False

        for result in results:
            if result == "CAVOK":
                cavok = True
            elif isinstance(result, Wind):
                wind = result
            elif isinstance(result, WindVariation):
                if wind is None:
                    raise InvalidReportError("wind variation without a preceding wind group")
                wind = replace(wind, variable_range=(result.from_direction, result.to_direction))
            elif isinstance(result, Visibility):
                visibility = result
            elif isinstance(result, CloudLayer):
                clouds.append(result)
            elif isinstance(result, VerticalVisibility):
                vertical_visibility = result
            elif isinstance(result, PresentWeather):
                weather.append(result)
            elif isinstance(result, Temperature):
                temperature = result
            elif isinstance(result, Pressure):
                pressure = result

        if wind is None:
            raise InvalidReportError("missing wind group")
        if temperature is None:
            raise InvalidReportError("missing temperature group")
        if pressure is None:
            raise InvalidReportError("missing pressure group")

        sky = None
        if clouds or vertical_visibility is not None:
            sky = SkyCondition(clouds=tuple(clouds), vertical_visibility=vertical_visibility)

        return Metar(
            raw_text=raw,
            station_id=header.station_id,
            observation_time=header.observation_time,
            auto=header.auto,
            corrected=header.corrected,
            conditions=WeatherConditions(
                wind=wind,
                cavok=cavok,
                visibility=visibility,
                sky=sky,
                weather=tuple(weather),
            ),
            temperature=temperature,
            pressure=pressure,
        )
