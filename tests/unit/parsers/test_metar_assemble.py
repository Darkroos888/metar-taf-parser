"""Behavioral tests for `MetarParser` assembly rules not covered by the integration samples.

Covers header variants (`SPECI`, missing report type, `COR` after the
timestamp), timestamp edge cases (a day that doesn't exist in the previous
month) and the errors raised for malformed reports:

- `UnknownTokenError` for a group no parser or flag recognises.
- `InvalidReportError` for a structurally broken report (missing station,
  timestamp, wind, temperature or pressure; impossible time; a wind
  variation without a wind group).

Both derive from `ParseError`, so callers can catch either with one `except`.
"""

from datetime import datetime, timezone

import pytest

from metar_taf_parser.exceptions import InvalidReportError, ParseError, UnknownTokenError
from metar_taf_parser.models import Wind


def _utc(year, month, day, hour, minute):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


class TestMetarHeaderVariants:
    """The header is `[METAR|SPECI] [COR] station DDHHMMZ`."""

    def test_accepts_speci_report_type(self, metar_parser, reference_time):
        """`SPECI` (special, unscheduled report) is read like `METAR`."""
        metar = metar_parser.parse("SPECI LEMD 161215Z 24010KT 18/12 Q1015", reference_time)
        assert metar.station_id == "LEMD"

    def test_report_type_is_optional(self, metar_parser, reference_time):
        """A report starting directly with the station id is accepted."""
        metar = metar_parser.parse("LEMD 161200Z 24010KT 18/12 Q1015", reference_time)
        assert metar.station_id == "LEMD"

    def test_cor_after_timestamp_marks_corrected(self, metar_parser, reference_time):
        """`COR` is also valid after the timestamp, not only before the station id."""
        metar = metar_parser.parse("METAR LEMD 161200Z COR 24010KT 18/12 Q1015", reference_time)
        assert metar.corrected is True

    def test_flags_default_to_false(self, metar_parser, reference_time):
        """Without `AUTO`, `COR` or `CAVOK`, all three flags are False."""
        metar = metar_parser.parse("METAR LEMD 161200Z 24010KT 18/12 Q1015", reference_time)
        assert metar.auto is False
        assert metar.corrected is False
        assert metar.conditions.cavok is False

    def test_wind_without_range_keeps_variable_range_none(self, metar_parser, reference_time):
        """`variable_range` is only filled when a `dddVddd` group follows the wind."""
        metar = metar_parser.parse("METAR LEMD 161200Z 24010KT 18/12 Q1015", reference_time)
        assert metar.conditions.wind == Wind(
            direction=240, speed=10, unit=metar.conditions.wind.unit
        )


class TestMetarTimestampEdgeCases:
    """Days that don't exist in the previous month keep stepping back."""

    @pytest.mark.parametrize(
        "time, reference, expected",
        [
            pytest.param(
                "302350Z",
                _utc(2027, 3, 1, 0, 10),
                _utc(2027, 1, 30, 23, 50),
                id="no-feb-30-goes-to-january",
            ),
            pytest.param(
                "312350Z",
                _utc(2027, 5, 1, 0, 10),
                _utc(2027, 3, 31, 23, 50),
                id="no-april-31-goes-to-march",
            ),
        ],
    )
    def test_steps_back_until_the_day_exists(self, metar_parser, time, reference, expected):
        """A day missing in the previous month resolves to the month before it."""
        raw = f"METAR LEMD {time} 24010KT 18/12 Q1015"
        assert metar_parser.parse(raw, reference).observation_time == expected


class TestMetarInvalidReports:
    """Structurally broken reports raise `InvalidReportError`."""

    INVALID = [
        pytest.param("", id="empty"),
        pytest.param("METAR 161200Z 24010KT 18/12 Q1015", id="missing-station"),
        pytest.param("METAR LEMD 24010KT 18/12 Q1015", id="missing-time"),
        pytest.param("METAR LEMD 161260Z 24010KT 18/12 Q1015", id="impossible-minute"),
        pytest.param("METAR LEMD 162500Z 24010KT 18/12 Q1015", id="impossible-hour"),
        pytest.param("METAR LEMD 161200Z 9999 18/12 Q1015", id="missing-wind"),
        pytest.param("METAR LEMD 161200Z 24010KT Q1015", id="missing-temperature"),
        pytest.param("METAR LEMD 161200Z 24010KT 18/12", id="missing-pressure"),
        pytest.param("METAR LEMD 161200Z 150V210 18/12 Q1015", id="variation-without-wind"),
    ]

    @pytest.mark.parametrize("raw", INVALID)
    def test_raises_invalid_report_error(self, metar_parser, reference_time, raw):
        """Missing or misplaced mandatory groups make the report invalid."""
        with pytest.raises(InvalidReportError):
            metar_parser.parse(raw, reference_time)


class TestMetarUnknownTokens:
    """A group that no parser or flag recognises raises `UnknownTokenError`."""

    @pytest.mark.parametrize("token", ["XYZ123", "BECMG", "R27/0900U"])
    def test_raises_unknown_token_error(self, metar_parser, reference_time, token):
        """The offending group is rejected instead of silently dropped."""
        raw = f"METAR LEMD 161200Z 24010KT {token} 18/12 Q1015"
        with pytest.raises(UnknownTokenError):
            metar_parser.parse(raw, reference_time)

    def test_errors_are_parse_errors(self, metar_parser, reference_time):
        """Both error types can be caught as `ParseError`."""
        with pytest.raises(ParseError):
            metar_parser.parse("METAR LEMD 161200Z 24010KT XYZ123 18/12 Q1015", reference_time)
