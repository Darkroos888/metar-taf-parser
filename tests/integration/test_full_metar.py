"""End-to-end tests: raw METAR text in, complete `Metar` value object out.

Each sample is a realistic report exercising a different combination of
groups. Unlike the unit suites, these go through the whole pipeline
(tokenize -> dispatch -> assemble), so they also pin down the decisions that
live in `MetarParser` rather than in any single `GroupParser`:

- `observation_time` is a UTC-aware `datetime`. Day/hour/minute come from the
  `DDHHMMZ` group; year and month from the `reference` passed to `parse()`
  (fixed to 2026-09-20 12:00Z here, see `conftest.py`). If the report's day is
  later than the reference's day, the report belongs to the previous month.
- Header and flag tokens without a `GroupParser` (`METAR`, station id,
  `DDHHMMZ`, `AUTO`, `COR`, `CAVOK`) are consumed by the report parser.
  `NOSIG` and the `=` end marker are ignored; `RMK ...` never reaches it.
- `CAVOK` sets `cavok=True` and leaves `visibility` and `sky` as `None`.
- Every cloud layer ends up, in order, in a single `SkyCondition`; `VVxxx`
  goes into that same `SkyCondition.vertical_visibility`.
- `210V270` (a `WindVariation`) fills the preceding `Wind.variable_range`,
  and the split tokens `1` + `1/2SM` become one `Visibility` of 1.5 SM.
- `raw_text` is the input exactly as given.
"""

from datetime import datetime, timezone

import pytest

from metar_taf_parser.enums import (
    CloudAmount,
    PressureUnit,
    VisibilityUnit,
    WeatherDescriptor,
    WeatherIntensity,
    WeatherPhenomenon,
    WindUnit,
)
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
)


def _utc(day, hour, minute, month=9, year=2026):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


CAVOK = "METAR LEMD 161200Z 24010KT CAVOK 18/12 Q1015 NOSIG="
US_WITH_REMARKS = (
    "METAR KJFK 161151Z 24010G18KT 10SM FEW050 SCT250 22/14 A2992 RMK AO2 SLP132 T02220139"
)
FOG_VERTICAL_VISIBILITY = "METAR LEVD 160600Z 00000KT 0100 FG VV001 M01/M01 Q1022"
AUTO_SNOW = "METAR EFHK 160920Z AUTO 35015G25KT 3000 -SN BKN008 OVC015 M05/M07 Q0998"
THUNDERSTORM_VARIABLE_WIND = (
    "METAR LEBL 161430Z 18012KT 150V210 6000 +TSRA FEW020CB BKN040 24/20 Q1009"
)
CORRECTED_FRACTIONAL_VISIBILITY = "METAR COR KORD 160356Z VRB03KT 1 1/2SM BR OVC004 M02/M03 A3012"

CASES = [
    pytest.param(
        CAVOK,
        Metar(
            raw_text=CAVOK,
            station_id="LEMD",
            observation_time=_utc(16, 12, 0),
            conditions=WeatherConditions(
                wind=Wind(direction=240, speed=10, unit=WindUnit.KT),
                cavok=True,
            ),
            temperature=Temperature(air=18, dew_point=12),
            pressure=Pressure(value=1015.0, unit=PressureUnit.HPA),
        ),
        id="cavok-nosig-end-marker",
    ),
    pytest.param(
        US_WITH_REMARKS,
        Metar(
            raw_text=US_WITH_REMARKS,
            station_id="KJFK",
            observation_time=_utc(16, 11, 51),
            conditions=WeatherConditions(
                wind=Wind(direction=240, speed=10, gust=18, unit=WindUnit.KT),
                visibility=Visibility(distance=10.0, unit=VisibilityUnit.STATUTE_MILES),
                sky=SkyCondition(
                    clouds=(
                        CloudLayer(amount=CloudAmount.FEW, height_ft=5000),
                        CloudLayer(amount=CloudAmount.SCT, height_ft=25000),
                    )
                ),
            ),
            temperature=Temperature(air=22, dew_point=14),
            pressure=Pressure(value=29.92, unit=PressureUnit.INHG),
        ),
        id="us-statute-miles-inhg-remarks",
    ),
    pytest.param(
        FOG_VERTICAL_VISIBILITY,
        Metar(
            raw_text=FOG_VERTICAL_VISIBILITY,
            station_id="LEVD",
            observation_time=_utc(16, 6, 0),
            conditions=WeatherConditions(
                wind=Wind(direction=0, speed=0, unit=WindUnit.KT),
                visibility=Visibility(distance=100, unit=VisibilityUnit.METERS),
                sky=SkyCondition(vertical_visibility=VerticalVisibility(height_ft=100)),
                weather=(
                    PresentWeather(
                        intensity=WeatherIntensity.MODERATE,
                        phenomena=(WeatherPhenomenon.FOG,),
                    ),
                ),
            ),
            temperature=Temperature(air=-1, dew_point=-1),
            pressure=Pressure(value=1022.0, unit=PressureUnit.HPA),
        ),
        id="fog-vertical-visibility-calm",
    ),
    pytest.param(
        AUTO_SNOW,
        Metar(
            raw_text=AUTO_SNOW,
            station_id="EFHK",
            observation_time=_utc(16, 9, 20),
            auto=True,
            conditions=WeatherConditions(
                wind=Wind(direction=350, speed=15, gust=25, unit=WindUnit.KT),
                visibility=Visibility(distance=3000, unit=VisibilityUnit.METERS),
                sky=SkyCondition(
                    clouds=(
                        CloudLayer(amount=CloudAmount.BKN, height_ft=800),
                        CloudLayer(amount=CloudAmount.OVC, height_ft=1500),
                    )
                ),
                weather=(
                    PresentWeather(
                        intensity=WeatherIntensity.LIGHT,
                        phenomena=(WeatherPhenomenon.SNOW,),
                    ),
                ),
            ),
            temperature=Temperature(air=-5, dew_point=-7),
            pressure=Pressure(value=998.0, unit=PressureUnit.HPA),
        ),
        id="auto-light-snow-negative-temps",
    ),
    pytest.param(
        THUNDERSTORM_VARIABLE_WIND,
        Metar(
            raw_text=THUNDERSTORM_VARIABLE_WIND,
            station_id="LEBL",
            observation_time=_utc(16, 14, 30),
            conditions=WeatherConditions(
                wind=Wind(
                    direction=180,
                    speed=12,
                    unit=WindUnit.KT,
                    variable_range=(150, 210),
                ),
                visibility=Visibility(distance=6000, unit=VisibilityUnit.METERS),
                sky=SkyCondition(
                    clouds=(
                        CloudLayer(amount=CloudAmount.FEW, height_ft=2000, convective_type="CB"),
                        CloudLayer(amount=CloudAmount.BKN, height_ft=4000),
                    )
                ),
                weather=(
                    PresentWeather(
                        intensity=WeatherIntensity.HEAVY,
                        phenomena=(WeatherPhenomenon.RAIN,),
                        descriptors=(WeatherDescriptor.THUNDERSTORM,),
                    ),
                ),
            ),
            temperature=Temperature(air=24, dew_point=20),
            pressure=Pressure(value=1009.0, unit=PressureUnit.HPA),
        ),
        id="thunderstorm-variable-wind-range",
    ),
    pytest.param(
        CORRECTED_FRACTIONAL_VISIBILITY,
        Metar(
            raw_text=CORRECTED_FRACTIONAL_VISIBILITY,
            station_id="KORD",
            observation_time=_utc(16, 3, 56),
            corrected=True,
            conditions=WeatherConditions(
                wind=Wind(direction=None, speed=3, unit=WindUnit.KT, variable=True),
                visibility=Visibility(distance=1.5, unit=VisibilityUnit.STATUTE_MILES),
                sky=SkyCondition(clouds=(CloudLayer(amount=CloudAmount.OVC, height_ft=400),)),
                weather=(
                    PresentWeather(
                        intensity=WeatherIntensity.MODERATE,
                        phenomena=(WeatherPhenomenon.MIST,),
                    ),
                ),
            ),
            temperature=Temperature(air=-2, dew_point=-3),
            pressure=Pressure(value=30.12, unit=PressureUnit.INHG),
        ),
        id="corrected-vrb-mixed-fraction-visibility",
    ),
]


class TestFullMetar:
    """Complete reports parse into the expected `Metar`."""

    @pytest.mark.parametrize("raw, expected", CASES)
    def test_parses_full_report(self, metar_parser, reference_time, raw, expected):
        """Every group of the report lands in the right field of the `Metar`."""
        assert metar_parser.parse(raw, reference=reference_time) == expected


class TestObservationTime:
    """Year and month of `observation_time` come from `reference`."""

    REPORT = "METAR LEMD {time} 24010KT CAVOK 18/12 Q1015"

    @pytest.mark.parametrize(
        "time, reference, expected",
        [
            pytest.param("161200Z", _utc(20, 12, 0), _utc(16, 12, 0), id="same-month"),
            pytest.param(
                "302330Z",
                _utc(1, 0, 30, month=10),
                _utc(30, 23, 30, month=9),
                id="previous-month",
            ),
            pytest.param(
                "312350Z",
                _utc(1, 0, 10, month=1, year=2027),
                _utc(31, 23, 50, month=12, year=2026),
                id="previous-year",
            ),
        ],
    )
    def test_completes_year_and_month_from_reference(self, metar_parser, time, reference, expected):
        """A report day later than the reference day belongs to the previous month."""
        metar = metar_parser.parse(self.REPORT.format(time=time), reference=reference)
        assert metar.observation_time == expected

    def test_reference_defaults_to_now_utc(self, metar_parser):
        """Without `reference`, the current UTC year and month are used."""
        now = datetime.now(timezone.utc)
        raw = self.REPORT.format(time=f"{now.day:02d}{now.hour:02d}00Z")
        metar = metar_parser.parse(raw)
        assert metar.observation_time == now.replace(minute=0, second=0, microsecond=0)
