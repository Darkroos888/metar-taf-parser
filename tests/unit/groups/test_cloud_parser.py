# tests/unit/groups/test_cloud_parser.py
"""Behavioral tests for `CloudParser` — the cloud layer METAR/TAF group.

Grammar covered:
- Amount code (`FEW`/`SCT`/`BKN`/`OVC`) + 3-digit height in hundreds of feet,
  with an optional convective-type suffix (`CB`, `TCU`), e.g. `BKN250CB`.
- The no-height amounts `SKC`/`CLR`/`NSC` (clear sky / no significant cloud),
  reported as a bare code with no digits and no convective type. These map
  to `height_ft=0` by convention since the raw token carries no height data.

Each class below isolates one piece of the grammar so a single failing rule
doesn't hide behind unrelated ones.
"""

import pytest

from metar_taf_parser.enums import CloudAmount
from metar_taf_parser.groups.clouds import CloudParser
from metar_taf_parser.models import CloudLayer


@pytest.fixture
def parser():
    """Provides a fresh instance of CloudParser for each test."""
    return CloudParser()


class TestCloudParserMatches:
    """`matches()` should accept valid cloud tokens and reject all others."""

    VALID_TOKENS = [
        "FEW020",
        "SCT100",
        "BKN008",
        "OVC250",
        "BKN250CB",
        "SCT035TCU",
        "SKC",
        "CLR",
        "NSC",
    ]

    NON_CLOUD_TOKENS = [
        "VV003",  # vertical visibility
        "9999",  # visibility
        "24010KT",  # wind
        "Q1015",  # pressure
        "18/12",  # temperature/dew point
        "CAVOK",
        "LEMD",  # station id
        "FEW02",  # only 2 height digits
        "FEW0200",  # 4 height digits
        "XXX020",  # unknown amount code
        "FEW020XX",  # unknown convective suffix
        "SKC020",  # SKC shouldn't carry a height
        "",
    ]

    @pytest.mark.parametrize("token", VALID_TOKENS)
    def test_accepts_valid_cloud_tokens(self, parser, token):
        """Tokens matching the amount+height (+convective) or bare no-height codes match."""
        assert parser.matches(token) is True

    @pytest.mark.parametrize("token", NON_CLOUD_TOKENS)
    def test_rejects_non_cloud_tokens(self, parser, token):
        """Tokens from other groups, or malformed cloud tokens, should not match."""
        assert parser.matches(token) is False


class TestCloudParserParsesAmountAndHeight:
    """Base case: amount code + 3-digit height, no convective type."""

    CASES = [
        ("FEW020", CloudLayer(amount=CloudAmount.FEW, height_ft=2000)),
        ("SCT100", CloudLayer(amount=CloudAmount.SCT, height_ft=10000)),
        ("BKN008", CloudLayer(amount=CloudAmount.BKN, height_ft=800)),
        ("OVC250", CloudLayer(amount=CloudAmount.OVC, height_ft=25000)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_amount_and_height(self, parser, token, expected):
        """Amount maps to the matching `CloudAmount`, height is read in hundreds of feet."""
        layer = parser.parse(token)
        assert layer == expected
        assert layer.convective_type is None


class TestCloudParserParsesConvectiveType:
    """Optional convective-type suffix (`CB`, `TCU`)."""

    CASES = [
        (
            "BKN250CB",
            CloudLayer(amount=CloudAmount.BKN, height_ft=25000, convective_type="CB"),
        ),
        (
            "SCT035TCU",
            CloudLayer(amount=CloudAmount.SCT, height_ft=3500, convective_type="TCU"),
        ),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_convective_type(self, parser, token, expected):
        """When the token includes a `CB`/`TCU` suffix, `convective_type` reflects it."""
        assert parser.parse(token) == expected

    def test_convective_type_defaults_to_none_when_absent(self, parser):
        """Without a convective suffix in the token, `convective_type` is None."""
        assert parser.parse("FEW020").convective_type is None


class TestCloudParserParsesSkyClearVariants:
    """No-height amounts: `SKC`, `CLR`, `NSC`."""

    CASES = [
        ("SKC", CloudLayer(amount=CloudAmount.SKC, height_ft=0)),
        ("CLR", CloudLayer(amount=CloudAmount.CLR, height_ft=0)),
        ("NSC", CloudLayer(amount=CloudAmount.NSC, height_ft=0)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_sky_clear_variant(self, parser, token, expected):
        """Bare no-height codes parse to `height_ft=0` and no convective type."""
        layer = parser.parse(token)
        assert layer == expected
        assert layer.convective_type is None
