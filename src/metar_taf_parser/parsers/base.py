"""Abstract report parser: tokenize, split header, dispatch to group parsers, assemble."""

import calendar
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime, timezone

from metar_taf_parser.exceptions import InvalidReportError, UnknownTokenError
from metar_taf_parser.groups.base import GroupParser
from metar_taf_parser.tokenizer import Tokenizer


class AbstractReportParser(ABC):
    """Template Method: `parse()` fixes the algorithm, subclasses fill in the hooks.

    `parse()` runs tokenize -> `_parse_header()` -> `_merge_fractions()` ->
    `_dispatch()` per body token -> `_assemble()`. Subclasses register their
    group parsers and override the two report-specific hooks, `_parse_header()`
    and `_assemble()`.
    """

    # Body keywords handled by `parse()` itself, never sent to `_dispatch()`.
    # Flag tokens are kept in `results` as plain strings, in token order, so
    # `_assemble()` knows where they appeared; ignored tokens are dropped.
    _FLAG_TOKENS = frozenset({"CAVOK"})
    _IGNORED_TOKENS = frozenset({"NOSIG"})

    def __init__(self, group_parsers: list[GroupParser]) -> None:
        """Store the group parsers that `_dispatch()` tries, in order.

        Args:
            group_parsers: Group parsers in dispatch priority order.
        """
        self._group_parsers = group_parsers
        self._tokenizer = Tokenizer()

    def parse(self, raw: str, reference: datetime | None = None) -> object:
        """Parse a raw report into its domain object.

        Report timestamps (`DDHHMMZ`) carry no year or month; they are taken
        from `reference`, rolling back a month when the report's day is later
        than the reference's day (e.g. a `302330Z` report read on the 1st).

        Args:
            raw: The raw report text.
            reference: UTC moment the report is read at. Defaults to now (UTC).

        Raises:
            InvalidReportError: If the report is structurally invalid.
            UnknownTokenError: If a body group is not recognised.
        """
        if reference is None:
            reference = datetime.now(timezone.utc)

        tokens = self._tokenizer.tokenize(raw)
        header, body = self._parse_header(tokens, reference)

        results: list[object] = []
        for token in self._merge_fractions(body):
            if token in self._IGNORED_TOKENS:
                continue
            if token in self._FLAG_TOKENS:
                results.append(token)
                continue
            results.append(self._dispatch(token))

        return self._assemble(raw, header, results, reference)

    def _merge_fractions(self, tokens: list[str]) -> Iterator[str]:
        """Yield `tokens` in order, rejoining split mixed statute-mile numbers.

        The tokenizer splits `1 1/2SM` into `1` and `1/2SM`; this generator
        yields them as the single token `"1 1/2SM"`. Only a whole number
        followed by a fraction ending in `SM` is rejoined: `9999 FEW020` or
        `9999 18/12` pass through unchanged. Lazy, single pass.

        Args:
            tokens: Body tokens, in report order.

        Yields:
            Each token, or a rejoined mixed-number visibility token.
        """
        whole: str | None = None
        for token in tokens:
            if whole is not None:
                if self._is_fraction_sm(token):
                    yield f"{whole} {token}"
                    whole = None
                    continue
                yield whole
                whole = None

            if token.isdigit():
                whole = token
            else:
                yield token

        if whole is not None:
            yield whole

    @staticmethod
    def _is_fraction_sm(token: str) -> bool:
        """Return True for a statute-mile fraction such as `1/2SM`."""
        if not token.endswith("SM"):
            return False
        numerator, slash, denominator = token.removesuffix("SM").partition("/")
        return bool(slash) and numerator.isdigit() and denominator.isdigit()

    def _dispatch(self, token: str) -> object:
        """Return the value object built by the first matching group parser.

        Raises:
            UnknownTokenError: If no group parser matches `token`.
        """
        for group_parser in self._group_parsers:
            if group_parser.matches(token):
                return group_parser.parse(token)
        raise UnknownTokenError(f"unrecognised group: {token!r}")

    @staticmethod
    def _complete_timestamp(day: int, hour: int, minute: int, reference: datetime) -> datetime:
        """Build a UTC `datetime` from a `DDHHMMZ` group, taking year/month from `reference`.

        If `day` is later than the reference's day, the report belongs to the
        previous month; months that don't have `day` are skipped backwards
        (e.g. day 30 read on March 1st resolves to January 30th).

        Raises:
            InvalidReportError: If the day, hour or minute is out of range.
        """
        if not 1 <= day <= 31 or hour > 23 or minute > 59:
            raise InvalidReportError(f"impossible time: day {day}, {hour:02d}:{minute:02d}")

        year, month = reference.year, reference.month
        if day > reference.day:
            year, month = AbstractReportParser._previous_month(year, month)
        while day > calendar.monthrange(year, month)[1]:
            year, month = AbstractReportParser._previous_month(year, month)

        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)

    @staticmethod
    def _previous_month(year: int, month: int) -> tuple[int, int]:
        """Return the (year, month) before the given one."""
        return (year - 1, 12) if month == 1 else (year, month - 1)

    @abstractmethod
    def _parse_header(self, tokens: list[str], reference: datetime) -> tuple[object, list[str]]:
        """Consume the report's leading header tokens.

        Args:
            tokens: All report tokens, in order.
            reference: UTC moment used to complete the header's timestamp.

        Returns:
            The parsed header and the remaining (body) tokens.

        Raises:
            InvalidReportError: If a mandatory header group is missing or invalid.
        """

    @abstractmethod
    def _assemble(
        self, raw: str, header: object, results: list[object], reference: datetime
    ) -> object:
        """Build the final report object from the header and the dispatched results.

        Args:
            raw: The raw report text.
            header: The header returned by `_parse_header()`.
            results: Value objects returned by `_dispatch()`, plus flag tokens
                (`_FLAG_TOKENS`) as plain strings, in token order.
            reference: UTC moment used to complete the report's timestamps.

        Raises:
            InvalidReportError: If a mandatory group is missing or misplaced.
        """
