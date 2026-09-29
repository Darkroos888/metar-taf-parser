"""Abstract report parser: tokenize, dispatch to group parsers, assemble."""

from abc import ABC, abstractmethod

from metar_taf_parser.groups.base import GroupParser
from metar_taf_parser.tokenizer import Tokenizer


class AbstractReportParser(ABC):
    """Template Method: `parse()` fixes the tokenize -> dispatch -> assemble algorithm.

    Subclasses register their group parsers and override the `_assemble()` hook.
    """

    def __init__(self, group_parsers: list[GroupParser]) -> None:
        """Store the group parsers that `_dispatch()` tries, in order.

        Args:
            group_parsers: Group parsers in dispatch priority order.
        """
        self._group_parsers = group_parsers
        self._tokenizer = Tokenizer()

    def parse(self, raw: str) -> object:
        """Parse a raw report into its domain object. Logic pending."""
        raise NotImplementedError

    def _dispatch(self, token: str) -> object:
        """Return the value object built by the first matching group parser. Logic pending."""
        raise NotImplementedError

    @abstractmethod
    def _assemble(self, raw: str, results: list[object]) -> object:
        """Build the final report object from the dispatched results."""
