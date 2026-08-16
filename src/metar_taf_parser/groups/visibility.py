"""Parser for the prevailing visibility METAR/TAF group."""

from metar_taf_parser.models import Visibility


class VisibilityParser:
    """Parses visibility tokens (e.g. 9999, 1/2SM) into a Visibility value object."""

    def matches(self, token: str) -> bool:
        """Return True if the token matches the visibility group pattern. Logic pending."""
        raise NotImplementedError

    def parse(self, token: str) -> Visibility:
        """Parse a visibility token into a Visibility instance. Logic pending."""
        raise NotImplementedError
