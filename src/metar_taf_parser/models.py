# src/metar_taf_parser/models.py
"""Domain value objects for METAR/TAF reports."""

from dataclasses import dataclass
from datetime import datetime

from metar_taf_parser.enums import (
    ChangeIndicator,
    CloudAmount,
    PressureUnit,
    VisibilityUnit,
    WeatherDescriptor,
    WeatherIntensity,
    WeatherPhenomenon,
    WindUnit,
)


@dataclass(frozen=True)
class VerticalVisibility:
    """Vertical visibility reported when the sky is obscured (e.g. VV003).

    `height_ft` is None when the height is reported but not measurable
    (`VV///`, typical of automated stations).
    """

    height_ft: int | None


@dataclass(frozen=True)
class Wind:
    """Surface wind: direction, speed, optional gust and variability."""

    direction: int | None
    speed: int
    unit: WindUnit
    gust: int | None = None
    variable: bool = False
    variable_range: tuple[int, int] | None = None


@dataclass(frozen=True)
class DirectionalVisibility:
    """Visibility reported toward a specific compass direction."""

    distance: float
    direction: str


@dataclass(frozen=True)
class Visibility:
    """Prevailing visibility, with optional directional variations.

    `distance` is a float so fractional statute-mile visibilities (e.g. `1/2SM`
    -> `0.5`) are representable alongside whole-unit meter/SM values.
    """

    distance: float
    unit: VisibilityUnit
    directional: tuple[DirectionalVisibility, ...] = ()


@dataclass(frozen=True)
class CloudLayer:
    """A single reported cloud layer."""

    amount: CloudAmount
    height_ft: int
    convective_type: str | None = None


@dataclass(frozen=True)
class SkyCondition:
    """Sky state: cloud layers, or vertical visibility if obscured."""

    clouds: tuple[CloudLayer, ...] = ()
    vertical_visibility: VerticalVisibility | None = None


@dataclass(frozen=True)
class PresentWeather:
    """A single present-weather group (e.g. +TSRA)."""

    intensity: WeatherIntensity
    phenomena: tuple[WeatherPhenomenon, ...]
    descriptors: tuple[WeatherDescriptor, ...] = ()


@dataclass(frozen=True)
class Temperature:
    """Air temperature and dew point, in whole degrees Celsius."""

    air: int
    dew_point: int


@dataclass(frozen=True)
class Pressure:
    """Atmospheric pressure (QNH/altimeter)."""

    value: float
    unit: PressureUnit


@dataclass(frozen=True)
class WeatherConditions:
    """A full set of observed/forecast conditions, shared by Metar and TafChangeGroup."""

    wind: Wind
    cavok: bool = False
    visibility: Visibility | None = None
    sky: SkyCondition | None = None
    weather: tuple[PresentWeather, ...] = ()


@dataclass(frozen=True)
class Metar:
    """A single METAR observation."""

    raw_text: str
    station_id: str
    observation_time: datetime
    conditions: WeatherConditions
    temperature: Temperature
    pressure: Pressure
    auto: bool = False
    corrected: bool = False


@dataclass(frozen=True)
class TafChangeGroup:
    """A single change period within a TAF (FM/BECMG/TEMPO/PROBxx)."""

    indicator: ChangeIndicator
    valid_from: datetime
    conditions: WeatherConditions
    valid_to: datetime | None = None
    probability: int | None = None


@dataclass(frozen=True)
class Taf:
    """A full TAF forecast: base conditions plus change groups."""

    raw_text: str
    station_id: str
    issue_time: datetime
    valid_from: datetime
    valid_to: datetime
    base_conditions: WeatherConditions
    change_groups: tuple[TafChangeGroup, ...] = ()
