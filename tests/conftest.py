"""Shared fixtures for the whole test suite."""

from datetime import datetime, timezone

import pytest

from metar_taf_parser.parsers.metar import MetarParser

# Fixed "now" for every integration test, so results don't depend on the day
# the suite runs. Report timestamps (`DDHHMMZ`) take their year/month from it.
REFERENCE_TIME = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)


def pytest_addoption(parser):
    """Add `--xfail-unimplemented`, used by CI while parsers are being written."""
    parser.addoption(
        "--xfail-unimplemented",
        action="store_true",
        help="Report tests that hit a NotImplementedError stub as xfail instead of failed.",
    )


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    """With `--xfail-unimplemented`, turn a NotImplementedError into an xfail.

    Only the stub's `NotImplementedError` is forgiven: once a parser has real
    code, its tests stop raising it and any failing assertion fails the run.
    Without the flag (the local default) red tests stay red, keeping the
    red -> green cycle visible.
    """
    try:
        return (yield)
    except NotImplementedError:
        if item.config.getoption("--xfail-unimplemented"):
            pytest.xfail("not implemented yet")
        raise


@pytest.fixture
def reference_time():
    """Fixed UTC moment the sample reports are read at (2026-09-20 12:00Z)."""
    return REFERENCE_TIME


@pytest.fixture
def metar_parser():
    """Provides a fresh instance of MetarParser for each test."""
    return MetarParser()
