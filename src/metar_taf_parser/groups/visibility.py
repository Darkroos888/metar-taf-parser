"""Parser for the prevailing visibility METAR/TAF group."""

import re
from fractions import Fraction

from metar_taf_parser.enums import VisibilityUnit
from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.models import Visibility


class VisibilityParser:
    """Parses visibility tokens (e.g. 9999, 1/2SM) into a Visibility value object."""

    # Either 4 digits (meters) or an optional M/P prefix + a statute-mile amount + `SM`.
    # The amount is a whole number (`10`), a fraction (`1/2`) or a mixed number
    # (`1 1/2`, rejoined by the report parser). Denominators never start with 0.
    _PATTERN = re.compile(
        r"(?P<meters>\d{4})"
        r"|(?P<prefix>[MP])?"
        r"(?P<miles>\d{1,2}|\d/[1-9]\d?|\d \d/[1-9]\d?)SM"
    )

    def matches(self, token: str) -> bool:
        """Return True if the token is a prevailing visibility group."""
        return self._PATTERN.fullmatch(token) is not None

    def parse(self, token: str) -> Visibility:
        """Parse a visibility token into a Visibility instance.

        The `M` ("less than") and `P` ("more than") prefixes are accepted but
        not stored: the model has no comparator field yet.

        Raises:
            ParseError: If the token is not a prevailing visibility group.
        """
        match = self._PATTERN.fullmatch(token)
        if match is None:
            raise ParseError(f"not a visibility group: {token!r}")

        meters = match.group("meters")
        if meters is not None:
            return Visibility(distance=int(meters), unit=VisibilityUnit.METERS)

        return Visibility(
            distance=self._statute_miles(match.group("miles")),
            unit=VisibilityUnit.STATUTE_MILES,
        )

    @staticmethod
    def _statute_miles(amount: str) -> float:
        """Convert `10`, `1/2` or `1 1/2` to a float (10.0, 0.5, 1.5)."""
        return float(sum(Fraction(part) for part in amount.split()))
