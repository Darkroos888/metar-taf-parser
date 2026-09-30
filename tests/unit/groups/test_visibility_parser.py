# tests/unit/groups/test_visibility_parser.py
"""Behavioral tests for `VisibilityParser` — the prevailing visibility METAR/TAF group.

Grammar covered:

- International format (meters): a 4-digit group, e.g. `9999`, `0800`,
  `0000`. `9999` conventionally means "10 km or more"; this parser stores it
  literally as `9999` rather than normalizing it, matching the raw-mapping
  approach used elsewhere (e.g. `TemperatureParser`).
- US format (statute miles): `TTSM` (whole number, e.g. `10SM`), `N/DSM`
  (simple fraction, e.g. `1/2SM`), `W N/DSM` (mixed number, e.g. `1 1/2SM`),
  and an optional `M` ("less than", e.g. `M1/4SM`) or `P` ("more than", e.g.
  `P6SM`) prefix. The prefix only affects `matches()` — the domain model has
  no comparator yet, so `parse()` keeps only the numeric value.

Known gap, intentionally deferred (same shape as the wind `210V270` case
documented in `CLAUDE.md`): the tokenizer splits a mixed statute-mile
number (`1 1/2SM`) into two tokens, `1` and `1/2SM`. Rejoining them is
`AbstractReportParser._dispatch()`'s job; this parser accepts the rejoined
`1 1/2SM` form, but never the bare whole number `1`. Directional variation
(`0800 1200NW`) is also a two-token construct left to `_dispatch()`: a lone
directional-variation token (e.g. `1200NW`) is non-matching, since parsing it
standalone would misrepresent it as a primary `Visibility`.

Each class below isolates one piece of the grammar so a single failing rule
doesn't hide behind unrelated ones.
"""

import pytest

from metar_taf_parser.enums import VisibilityUnit
from metar_taf_parser.groups.visibility import VisibilityParser
from metar_taf_parser.models import Visibility


@pytest.fixture
def parser():
    """Provides a fresh instance of VisibilityParser for each test."""
    return VisibilityParser()


class TestVisibilityParserMatchesMeters:
    """`matches()` should accept the 4-digit international (meters) format."""

    VALID_TOKENS = [
        "9999",
        "0800",
        "0350",
        "0000",
        "1000",
    ]

    @pytest.mark.parametrize("token", VALID_TOKENS)
    def test_accepts_valid_meters_tokens(self, parser, token):
        """A plain 4-digit group should match as meters visibility."""
        assert parser.matches(token) is True


class TestVisibilityParserMatchesStatuteMiles:
    """`matches()` should accept the US statute-mile format, single token only."""

    VALID_TOKENS = [
        "10SM",
        "P6SM",
        "1SM",
        "1 1/2SM",
        "1/2SM",
        "3/4SM",
        "1/4SM",
        "M1/4SM",
        "M1/2SM",
    ]

    @pytest.mark.parametrize("token", VALID_TOKENS)
    def test_accepts_valid_statute_mile_tokens(self, parser, token):
        """Whole, simple-fraction, and `M`-prefixed SM tokens should match."""
        assert parser.matches(token) is True


class TestVisibilityParserRejectsDirectionalOnlyTokens:
    """A lone direction-qualified variation token should not match on its own."""

    DIRECTIONAL_ONLY_TOKENS = [
        "1200NW",
        "0800N",
        "1500SE",
    ]

    @pytest.mark.parametrize("token", DIRECTIONAL_ONLY_TOKENS)
    def test_rejects_directional_only_tokens(self, parser, token):
        """These only make sense combined with a preceding main visibility token."""
        assert parser.matches(token) is False


class TestVisibilityParserRejectsRWYOnlyTokens:
    """Runway visual range (RVR) groups are a different group, not prevailing visibility."""

    RWY_ONLY_TOKENS = [
        "R27/0900U",
        "R17R/1300N",
        "R03L/0800D",
        "R12C/P2000",
        "R35/M0050",
        "R26/1100FT",
        "R10L/M0600FT",
        "R03/0900FT",
        "R22R/P6000FT",
        "R16C/0600V1000FT",
    ]

    @pytest.mark.parametrize("token", RWY_ONLY_TOKENS)
    def test_rejects_rwy_only_tokens(self, parser, token):
        """`Rxx/...` tokens describe a single runway and are out of scope."""
        assert parser.matches(token) is False


class TestVisibilityParserRejectsNonVisibilityTokens:
    """`matches()` should reject tokens from other groups and malformed visibility."""

    NON_VISIBILITY_TOKENS = [
        "24010KT",  # wind
        "FEW020",  # cloud layer
        "VV003",  # vertical visibility
        "Q1015",  # pressure
        "18/12",  # temperature
        "CAVOK",  # ceiling and visibility OK
        "AUTO",  # automated message
        "LEMD",  # station id
        "999",  # meters, too few digits
        "99999",  # meters, too many digits
        "SM",  # missing distance
        "1/2",  # fraction without SM suffix
        "ABCDSM",  # non-numeric
        "1",  # bare whole number: first half of a split `1 1/2SM`
        "11/2SM",  # mixed number without the separating space
        "1/0SM",  # zero denominator
        "PM1SM",  # two prefixes
        "",
    ]

    @pytest.mark.parametrize("token", NON_VISIBILITY_TOKENS)
    def test_rejects_non_visibility_tokens(self, parser, token):
        """Tokens from other groups, or malformed visibility, should not match."""
        assert parser.matches(token) is False


class TestVisibilityParserParsesMeters:
    """Parsing the international (meters) format."""

    CASES = [
        ("9999", Visibility(distance=9999, unit=VisibilityUnit.METERS)),
        ("0800", Visibility(distance=800, unit=VisibilityUnit.METERS)),
        ("0350", Visibility(distance=350, unit=VisibilityUnit.METERS)),
        ("0000", Visibility(distance=0, unit=VisibilityUnit.METERS)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_meters_tokens(self, parser, token, expected):
        """The 4 digits map directly to `distance`, in meters, unnormalized."""
        assert parser.parse(token) == expected

    def test_defaults_to_no_directional_variation(self, parser):
        """A single meters token carries no directional variation by itself."""
        assert parser.parse("9999").directional == ()


class TestVisibilityParserParsesStatuteMilesWhole:
    """Parsing whole statute-mile values."""

    CASES = [
        ("10SM", Visibility(distance=10.0, unit=VisibilityUnit.STATUTE_MILES)),
        ("1SM", Visibility(distance=1.0, unit=VisibilityUnit.STATUTE_MILES)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_whole_statute_miles(self, parser, token, expected):
        """A whole number before `SM` maps directly to `distance`."""
        assert parser.parse(token) == expected


class TestVisibilityParserParsesStatuteMilesFractional:
    """Parsing fractional statute-mile values (`N/DSM`)."""

    CASES = [
        ("1/2SM", Visibility(distance=0.5, unit=VisibilityUnit.STATUTE_MILES)),
        ("3/4SM", Visibility(distance=0.75, unit=VisibilityUnit.STATUTE_MILES)),
        ("1/4SM", Visibility(distance=0.25, unit=VisibilityUnit.STATUTE_MILES)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_fractional_statute_miles(self, parser, token, expected):
        """The fraction is converted to its decimal value in `distance`."""
        assert parser.parse(token) == expected


class TestVisibilityParserParsesStatuteMilesLessThanPrefix:
    """The `M` prefix ("less than") parses to the same numeric value as the fraction."""

    CASES = [
        ("M1/4SM", Visibility(distance=0.25, unit=VisibilityUnit.STATUTE_MILES)),
        ("M1/2SM", Visibility(distance=0.5, unit=VisibilityUnit.STATUTE_MILES)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_less_than_prefix(self, parser, token, expected):
        """`M` is a comparator qualifier not yet modeled; only the value is kept."""
        assert parser.parse(token) == expected


class TestVisibilityParserParsesStatuteMilesMixedNumber:
    """Parsing a mixed statute-mile number (`W N/DSM`), rejoined by `_dispatch()`."""

    CASES = [
        ("1 1/2SM", Visibility(distance=1.5, unit=VisibilityUnit.STATUTE_MILES)),
        ("2 3/4SM", Visibility(distance=2.75, unit=VisibilityUnit.STATUTE_MILES)),
    ]

    @pytest.mark.parametrize("token, expected", CASES)
    def test_parses_mixed_number(self, parser, token, expected):
        """Whole part plus fraction, e.g. `1 1/2SM` -> 1.5."""
        assert parser.parse(token) == expected


class TestVisibilityParserParsesStatuteMilesMoreThanPrefix:
    """The `P` prefix ("more than") parses to the plain numeric value."""

    def test_parses_more_than_prefix(self, parser):
        """`P6SM` (more than 6 SM) keeps only the value, like the `M` prefix."""
        assert parser.parse("P6SM") == Visibility(distance=6.0, unit=VisibilityUnit.STATUTE_MILES)
