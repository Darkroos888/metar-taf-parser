"""Enumerations used across the METAR/TAF domain model."""

from enum import Enum


class WindUnit(Enum):
    """Unit in which wind speed is reported."""

    KT = "KT"
    MPS = "MPS"
    KMH = "KMH"


class VisibilityUnit(Enum):
    """Unit in which visibility distance is reported."""

    METERS = "M"
    STATUTE_MILES = "SM"


class CloudAmount(Enum):
    """Sky coverage amount for a cloud layer."""

    FEW = "FEW"
    SCT = "SCT"
    BKN = "BKN"
    OVC = "OVC"
    SKC = "SKC"
    CLR = "CLR"
    NSC = "NSC"


class PressureUnit(Enum):
    """Unit in which atmospheric pressure is reported."""

    HPA = "Q"
    INHG = "A"


class WeatherIntensity(Enum):
    """Intensity qualifier of a present-weather group."""

    LIGHT = "-"
    MODERATE = ""
    HEAVY = "+"
    IN_VICINITY = "VC"


class WeatherDescriptor(Enum):
    """Descriptor qualifier of a present-weather group."""

    SHOWERS = "SH"
    THUNDERSTORM = "TS"
    FREEZING = "FZ"
    DRIFTING = "DR"
    BLOWING = "BL"
    PATCHES = "BC"
    PARTIAL = "PR"
    SHALLOW = "MI"


class WeatherPhenomenon(Enum):
    """Weather phenomenon code within a present-weather group."""

    RAIN = "RA"
    DRIZZLE = "DZ"
    SNOW = "SN"
    SNOW_GRAINS = "SG"
    ICE_PELLETS = "PL"
    HAIL = "GR"
    SMALL_HAIL = "GS"
    FOG = "FG"
    MIST = "BR"
    HAZE = "HZ"
    DUST = "DU"
    SAND = "SA"
    SMOKE = "FU"
    VOLCANIC_ASH = "VA"
    DUST_STORM = "DS"
    SAND_STORM = "SS"
    SQUALLS = "SQ"
    FUNNEL_CLOUD = "FC"


class ChangeIndicator(Enum):
    """TAF change-group indicator."""

    FM = "FM"
    BECMG = "BECMG"
    TEMPO = "TEMPO"
    PROB30 = "PROB30"
    PROB40 = "PROB40"
