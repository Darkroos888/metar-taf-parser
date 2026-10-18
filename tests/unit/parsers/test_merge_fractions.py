"""Behavioral tests for `AbstractReportParser._merge_fractions()`.

The tokenizer splits a mixed statute-mile visibility (`1 1/2SM`) into two
tokens. `_merge_fractions()` rejoins them before dispatch, so
`VisibilityParser` sees `"1 1/2SM"`. Only a whole number followed by a
fraction ending in `SM` is rejoined; every other token passes through
unchanged and in order. It is a lazy generator (single pass).
"""

from collections.abc import Iterator

import pytest


class TestMergeFractionsRejoins:
    """A whole number followed by an `N/DSM` fraction becomes one token."""

    @pytest.mark.parametrize(
        ("tokens", "expected"),
        [
            pytest.param(["1", "1/2SM"], ["1 1/2SM"], id="one-and-a-half"),
            pytest.param(["2", "3/4SM"], ["2 3/4SM"], id="two-and-three-quarters"),
            pytest.param(
                ["VRB03KT", "1", "1/2SM", "BR", "OVC004"],
                ["VRB03KT", "1 1/2SM", "BR", "OVC004"],
                id="in-the-middle-of-a-body",
            ),
            pytest.param(
                ["1", "1/4SM", "2", "1/2SM"],
                ["1 1/4SM", "2 1/2SM"],
                id="two-consecutive-merges",
            ),
        ],
    )
    def test_rejoins_mixed_number(self, metar_parser, tokens, expected):
        assert list(metar_parser._merge_fractions(tokens)) == expected


class TestMergeFractionsLeavesOtherTokens:
    """Anything that isn't `whole number` + `fraction SM` passes through as is."""

    @pytest.mark.parametrize(
        "tokens",
        [
            pytest.param([], id="empty"),
            pytest.param(["24010KT", "9999", "FEW020"], id="meters-then-cloud"),
            pytest.param(["9999", "18/12", "Q1015"], id="digits-then-temperature"),
            pytest.param(["24010KT", "1/2SM", "BR"], id="simple-fraction-alone"),
            pytest.param(["24010KT", "10SM", "FEW050"], id="whole-miles"),
            pytest.param(["24010KT", "1"], id="trailing-whole-number"),
            pytest.param(["24010KT", "1", "FEW020"], id="whole-number-then-non-fraction"),
        ],
    )
    def test_passes_through_unchanged(self, metar_parser, tokens):
        assert list(metar_parser._merge_fractions(tokens)) == tokens


class TestMergeFractionsIsAGenerator:
    """Tokens are produced lazily, not as a pre-built list."""

    def test_returns_an_iterator(self, metar_parser):
        result = metar_parser._merge_fractions(["24010KT", "9999"])
        assert isinstance(result, Iterator)
        assert not isinstance(result, list)
