# tests/unit/test_models.py
"""Structural and behavioral tests for domain value objects.

These tests check *shape*: immutability, value equality, hashability, and
sensible defaults. They know nothing about parsing logic.
"""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime

import pytest

from metar_taf_parser.enums import (
    ChangeIndicator,
    CloudAmount,
    PressureUnit,
    VisibilityUnit,
    WeatherIntensity,
    WeatherPhenomenon,
    WindUnit,
)
from metar_taf_parser.models import (
    CloudLayer,
    DirectionalVisibility,
    Metar,
    PresentWeather,
    Pressure,
    SkyCondition,
    Taf,
    TafChangeGroup,
    Temperature,
    VerticalVisibility,
    Visibility,
    WeatherConditions,
    Wind,
    WindVariation,
)

_SAMPLE_WIND = Wind(direction=240, speed=10, unit=WindUnit.KT)
_SAMPLE_VISIBILITY = Visibility(distance=9999, unit=VisibilityUnit.METERS)
_SAMPLE_SKY = SkyCondition(clouds=(CloudLayer(amount=CloudAmount.FEW, height_ft=2000),))
_SAMPLE_CONDITIONS = WeatherConditions(
    wind=_SAMPLE_WIND,
    visibility=_SAMPLE_VISIBILITY,
    sky=_SAMPLE_SKY,
)
_SAMPLE_TEMPERATURE = Temperature(air=18, dew_point=12)
_SAMPLE_PRESSURE = Pressure(value=1015.0, unit=PressureUnit.HPA)
_SAMPLE_TIME = datetime(2026, 8, 16, 12, 0)


FROZEN_VALUE_OBJECTS = [
    (VerticalVisibility, {"height_ft": 300}),
    (Wind, {"direction": 240, "speed": 10, "unit": WindUnit.KT}),
    (WindVariation, {"from_direction": 100, "to_direction": 180}),
    (DirectionalVisibility, {"distance": 5000, "direction": "NE"}),
    (Visibility, {"distance": 9999, "unit": VisibilityUnit.METERS}),
    (CloudLayer, {"amount": CloudAmount.FEW, "height_ft": 2000}),
    (SkyCondition, {"clouds": (CloudLayer(amount=CloudAmount.FEW, height_ft=2000),)}),
    (
        PresentWeather,
        {"intensity": WeatherIntensity.MODERATE, "phenomena": (WeatherPhenomenon.RAIN,)},
    ),
    (Temperature, {"air": 18, "dew_point": 12}),
    (Pressure, {"value": 1015.0, "unit": PressureUnit.HPA}),
    (
        WeatherConditions,
        {"wind": _SAMPLE_WIND, "visibility": _SAMPLE_VISIBILITY, "sky": _SAMPLE_SKY},
    ),
    (
        Metar,
        {
            "raw_text": "METAR LEMD 161200Z 24010KT 9999 FEW020 18/12 Q1015",
            "station_id": "LEMD",
            "observation_time": _SAMPLE_TIME,
            "conditions": _SAMPLE_CONDITIONS,
            "temperature": _SAMPLE_TEMPERATURE,
            "pressure": _SAMPLE_PRESSURE,
        },
    ),
    (
        TafChangeGroup,
        {
            "indicator": ChangeIndicator.FM,
            "valid_from": _SAMPLE_TIME,
            "conditions": _SAMPLE_CONDITIONS,
        },
    ),
    (
        Taf,
        {
            "raw_text": "TAF LEMD 161100Z 1612/1712 24010KT 9999 FEW020",
            "station_id": "LEMD",
            "issue_time": _SAMPLE_TIME,
            "valid_from": _SAMPLE_TIME,
            "valid_to": _SAMPLE_TIME,
            "base_conditions": _SAMPLE_CONDITIONS,
        },
    ),
]


@pytest.mark.parametrize("cls, kwargs", FROZEN_VALUE_OBJECTS)
class TestFrozenValueObjectContract:
    """Contrato estructural compartido por las 14 clases de dominio."""

    def test_constructs_with_given_values(self, cls, kwargs):
        """Cada kwarg pasado al constructor se refleja en el atributo."""
        instance = cls(**kwargs)
        for attr_name, value in kwargs.items():
            assert getattr(instance, attr_name) == value

    def test_is_immutable(self, cls, kwargs):
        """No se puede reasignar ningún atributo tras la construcción."""
        instance = cls(**kwargs)
        first_field = fields(instance)[0].name
        with pytest.raises(FrozenInstanceError):
            # noinspection PyDataclass
            setattr(instance, first_field, getattr(instance, first_field))

    def test_equality_is_by_value_not_identity(self, cls, kwargs):
        """Dos instancias con los mismos valores son iguales."""
        assert cls(**kwargs) == cls(**kwargs)

    def test_is_hashable(self, cls, kwargs):
        """Necesario para anidarlas dentro de otras dataclasses frozen."""
        assert hash(cls(**kwargs)) == hash(cls(**kwargs))


class TestDomainModelDefaults:
    """Verifica el valor por defecto de los campos opcionales."""

    def test_wind_defaults(self):
        """Wind sin ráfaga ni variabilidad por defecto."""
        wind = Wind(direction=240, speed=10, unit=WindUnit.KT)
        assert wind.gust is None
        assert wind.variable is False
        assert wind.variable_range is None

    def test_visibility_defaults_to_no_directional_readings(self):
        """Visibility sin lecturas direccionales por defecto."""
        visibility = Visibility(distance=9999, unit=VisibilityUnit.METERS)
        assert visibility.directional == ()

    def test_visibility_accepts_fractional_statute_miles(self):
        """Visibility admite distancias fraccionarias (p. ej. `1/2SM` -> 0.5)."""
        visibility = Visibility(distance=0.5, unit=VisibilityUnit.STATUTE_MILES)
        assert visibility.distance == 0.5

    def test_directional_visibility_accepts_fractional_distance(self):
        """DirectionalVisibility admite distancias fraccionarias."""
        directional = DirectionalVisibility(distance=1.5, direction="NE")
        assert directional.distance == 1.5

    def test_cloud_layer_defaults_to_no_convective_type(self):
        """CloudLayer sin tipo convectivo por defecto."""
        layer = CloudLayer(amount=CloudAmount.FEW, height_ft=2000)
        assert layer.convective_type is None

    def test_sky_condition_defaults_to_empty(self):
        """SkyCondition vacío por defecto (ni nubes ni VV)."""
        sky = SkyCondition()
        assert sky.clouds == ()
        assert sky.vertical_visibility is None

    def test_present_weather_defaults_to_no_descriptors(self):
        """PresentWeather sin descriptores por defecto (p. ej. `-RA`)."""
        weather = PresentWeather(
            intensity=WeatherIntensity.LIGHT,
            phenomena=(WeatherPhenomenon.RAIN,),
        )
        assert weather.descriptors == ()

    def test_weather_conditions_defaults(self):
        """WeatherConditions sin CAVOK, visibilidad, cielo ni fenómenos por defecto."""
        conditions = WeatherConditions(wind=_SAMPLE_WIND)
        assert conditions.cavok is False
        assert conditions.visibility is None
        assert conditions.sky is None
        assert conditions.weather == ()

    def test_metar_defaults_to_not_auto_not_corrected(self):
        """Metar no es AUTO ni COR por defecto."""
        metar = Metar(
            raw_text="...",
            station_id="LEMD",
            observation_time=_SAMPLE_TIME,
            conditions=_SAMPLE_CONDITIONS,
            temperature=_SAMPLE_TEMPERATURE,
            pressure=_SAMPLE_PRESSURE,
        )
        assert metar.auto is False
        assert metar.corrected is False

    def test_taf_change_group_defaults(self):
        """TafChangeGroup sin fin de validez ni probabilidad por defecto."""
        change = TafChangeGroup(
            indicator=ChangeIndicator.FM,
            valid_from=_SAMPLE_TIME,
            conditions=_SAMPLE_CONDITIONS,
        )
        assert change.valid_to is None
        assert change.probability is None

    def test_taf_defaults_to_no_change_groups(self):
        """Taf sin grupos de cambio por defecto."""
        taf = Taf(
            raw_text="...",
            station_id="LEMD",
            issue_time=_SAMPLE_TIME,
            valid_from=_SAMPLE_TIME,
            valid_to=_SAMPLE_TIME,
            base_conditions=_SAMPLE_CONDITIONS,
        )
        assert taf.change_groups == ()
