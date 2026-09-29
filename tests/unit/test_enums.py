"""Tests for the enum values used across the domain model.

Each enum's `.value` is the literal code as it appears in a METAR/TAF report,
so group parsers can map a matched substring straight to a member via
`EnumClass(code)`. These tests pin that mapping so a typo in a value surfaces
here instead of as an obscure parser failure.
"""

import pytest

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

REPORT_CODES = {
    WindUnit: {
        "KT": WindUnit.KT,
        "MPS": WindUnit.MPS,
        "KMH": WindUnit.KMH,
    },
    VisibilityUnit: {
        "M": VisibilityUnit.METERS,
        "SM": VisibilityUnit.STATUTE_MILES,
    },
    CloudAmount: {
        "FEW": CloudAmount.FEW,
        "SCT": CloudAmount.SCT,
        "BKN": CloudAmount.BKN,
        "OVC": CloudAmount.OVC,
        "SKC": CloudAmount.SKC,
        "CLR": CloudAmount.CLR,
        "NSC": CloudAmount.NSC,
    },
    PressureUnit: {
        "Q": PressureUnit.HPA,
        "A": PressureUnit.INHG,
    },
    WeatherIntensity: {
        "-": WeatherIntensity.LIGHT,
        "": WeatherIntensity.MODERATE,
        "+": WeatherIntensity.HEAVY,
        "VC": WeatherIntensity.IN_VICINITY,
    },
    WeatherDescriptor: {
        "SH": WeatherDescriptor.SHOWERS,
        "TS": WeatherDescriptor.THUNDERSTORM,
        "FZ": WeatherDescriptor.FREEZING,
        "DR": WeatherDescriptor.DRIFTING,
        "BL": WeatherDescriptor.BLOWING,
        "BC": WeatherDescriptor.PATCHES,
        "PR": WeatherDescriptor.PARTIAL,
        "MI": WeatherDescriptor.SHALLOW,
    },
    WeatherPhenomenon: {
        "RA": WeatherPhenomenon.RAIN,
        "DZ": WeatherPhenomenon.DRIZZLE,
        "SN": WeatherPhenomenon.SNOW,
        "SG": WeatherPhenomenon.SNOW_GRAINS,
        "PL": WeatherPhenomenon.ICE_PELLETS,
        "GR": WeatherPhenomenon.HAIL,
        "GS": WeatherPhenomenon.SMALL_HAIL,
        "FG": WeatherPhenomenon.FOG,
        "BR": WeatherPhenomenon.MIST,
        "HZ": WeatherPhenomenon.HAZE,
        "DU": WeatherPhenomenon.DUST,
        "SA": WeatherPhenomenon.SAND,
        "FU": WeatherPhenomenon.SMOKE,
        "VA": WeatherPhenomenon.VOLCANIC_ASH,
        "DS": WeatherPhenomenon.DUST_STORM,
        "SS": WeatherPhenomenon.SAND_STORM,
        "SQ": WeatherPhenomenon.SQUALLS,
        "FC": WeatherPhenomenon.FUNNEL_CLOUD,
    },
    ChangeIndicator: {
        "FM": ChangeIndicator.FM,
        "BECMG": ChangeIndicator.BECMG,
        "TEMPO": ChangeIndicator.TEMPO,
        "PROB30": ChangeIndicator.PROB30,
        "PROB40": ChangeIndicator.PROB40,
    },
}

CODE_CASES = [
    pytest.param(enum_cls, code, member, id=f"{enum_cls.__name__}-{code or 'empty'}")
    for enum_cls, mapping in REPORT_CODES.items()
    for code, member in mapping.items()
]


@pytest.mark.parametrize("enum_cls, code, member", CODE_CASES)
def test_report_code_maps_to_member(enum_cls, code, member):
    """El código tal como aparece en el parte resuelve al miembro correcto."""
    assert enum_cls(code) is member


@pytest.mark.parametrize("enum_cls", REPORT_CODES, ids=lambda cls: cls.__name__)
def test_every_member_is_covered(enum_cls):
    """La tabla cubre todos los miembros: añadir uno sin su código hace fallar el test."""
    assert set(REPORT_CODES[enum_cls].values()) == set(enum_cls)


@pytest.mark.parametrize("enum_cls", REPORT_CODES, ids=lambda cls: cls.__name__)
def test_values_are_unique(enum_cls):
    """Sin valores duplicados: un duplicado crearía un alias silencioso en Enum."""
    assert len(enum_cls.__members__) == len(enum_cls)


@pytest.mark.parametrize("enum_cls", REPORT_CODES, ids=lambda cls: cls.__name__)
def test_unknown_code_raises_value_error(enum_cls):
    """Un código desconocido no resuelve a ningún miembro."""
    with pytest.raises(ValueError):
        enum_cls("XXXXX")
