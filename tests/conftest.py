"""Shared fixtures for the whole test suite."""

from datetime import datetime, timezone

import pytest

from metar_taf_parser.parsers.metar import MetarParser

# Fixed "now" for every integration test, so results don't depend on the day
# the suite runs. Report timestamps (`DDHHMMZ`) take their year/month from it.
REFERENCE_TIME = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def reference_time():
    """Fixed UTC moment the sample reports are read at (2026-09-20 12:00Z)."""
    return REFERENCE_TIME


@pytest.fixture
def metar_parser():
    """Provides a fresh instance of MetarParser for each test."""
    return MetarParser()
