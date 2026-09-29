"""Behavioral tests for `Tokenizer` — splitting a raw report into its groups.

Rules covered:
- Groups are separated by any run of whitespace (spaces, tabs, newlines):
  reports copied from bulletins are often wrapped over several lines.
- The ICAO end-of-report marker `=` is dropped, whether glued to the last
  group (`Q1015=`) or standing alone.
- The `RMK` group and everything after it (remarks) are discarded. Remarks
  are out of scope for now.
- Otherwise tokens come back unchanged and in order: the tokenizer doesn't
  interpret, merge or filter groups. Header tokens (`METAR`, station id),
  flags (`AUTO`, `CAVOK`, `NOSIG`) and two-token constructs (`1 1/2SM`,
  `24010KT 210V270`) are the report parser's job.
"""

import pytest

from metar_taf_parser.tokenizer import Tokenizer


@pytest.fixture
def tokenizer():
    """Provides a fresh instance of Tokenizer for each test"""
    return Tokenizer()


class TestTokenizerSplitsOnWhitespace:
    """Any run of whitespace separates two groups."""

    def test_splits_a_full_report_on_spaces(self, tokenizer):
        """A single-line report splits into its groups, in order."""
        raw = "METAR LEMD 161200Z 24010KT 9999 FEW020 18/12 Q1015"
        assert tokenizer.tokenize(raw) == [
            "METAR",
            "LEMD",
            "161200Z",
            "24010KT",
            "9999",
            "FEW020",
            "18/12",
            "Q1015",
        ]

    @pytest.mark.parametrize(
        "raw",
        [
            "LEMD  161200Z   24010KT",  # repeate spaces
            "LEMD\t161200Z\t24010KT",  # tabs
            "LEMD\n161200Z\n24010KT",  # wrapped
            "LEMD 161200Z\r\n24010KT",  # Windows line ending
            "  LEMD 161200Z 24010KT  ",  # leadin
        ],
    )
    def test_any_whitespace_run_is_a_single_separator(self, tokenizer, raw):
        """Mixed or repeated whitespace never produces empty tokens."""
        assert tokenizer.tokenize(raw) == ["LEMD", "161200Z", "24010KT"]


class TestTokenizerDropsEndMarker:
    """The `=` end-of-report marker is not a group."""

    @pytest.mark.parametrize(
        "raw",
        [
            "LEMD 18/12 Q1015=",  # glued to the last group
            "LEMD 18/12 Q1015 =",  # standalone
            "LEMD 18/12 Q1015\n=",  # on its own
        ],
    )
    def test_drops_end_marker(self, tokenizer, raw):
        """The trailing `=` disappears and the last group stays intact."""
        assert tokenizer.tokenize(raw) == ["LEMD", "18/12", "Q1015"]


class TestTokenizerDropsRemarks:
    """`RMK` and everything after it are discarded."""

    def test_discards_rmk_and_everything_after(self, tokenizer):
        """US-style remarks after `RMK` don't reach the parser."""
        raw = "METAR KJFK 161151Z 24010KT 10SM FE132 T01830122"
        assert tokenizer.tokenize(raw) == [
            "METAR",
            "KJFK",
            "161151Z",
            "24010KT",
            "10SM",
            "FEW250",
            "18/12",
            "A2992",
        ]

    def test_discards_remarks_ending_with_end_marker(self, tokenizer):
        """Remarks followed by `=` are discarded along with the marker."""
        assert tokenizer.tokenize("KJFK 18/12 A2992 RMK AO2 SLP132=") == [
            "KJFK",
            "18/12",
            "A2992",
        ]

    def test_bare_rmk_at_the_end_is_discarded(self, tokenizer):
        """A trailing `RMK` with no remarks after it is still dropped."""
        assert tokenizer.tokenize("LEMD 18/12 Q1015 RMK") == ["LEMD", "18/12", "Q1015"]


class TestTokenizerKeepsTokensUnchanged:
    """The tokenizer doesn't interpret, merge or filter groups."""

    def test_keeps_header_and_flag_tokens(self, tokenizer):
        """`METAR`, `COR`, `AUTO`, `CAVOK`, `NOSIG` come through as plain tokens."""
        raw = "METAR COR LEMD 161200Z AUTO 24010KT CAVOK 18/12 Q1015 NOSIG"
        assert tokenizer.tokenize(raw) == raw.split(" ")

    def test_does_not_merge_multi_token_groups(self, tokenizer):
        """`1 1/2SM` and `24010KT 210V270` stay as separate tokens."""
        assert tokenizer.tokenize("KJFK 24010KT 210V270 1 1/2SM") == [
            "KJFK",
            "24010KT",
            "210V270",
            "1",
            "1/2SM",
        ]


class TestTokenizerEmptyInput:
    """Reports with no groups yield an empty list."""

    @pytest.mark.parametrize("raw", ["", "   ", "\n", "="])
    def test_empty_report_yields_no_tokens(self, tokenizer, raw):
        """Blank input, or only the end marker, gives `[]`."""
        assert tokenizer.tokenize(raw) == []
