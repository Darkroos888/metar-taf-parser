"""Parser for the vertical visibility (VVxxx) METAR/TAF group."""

from metar_taf_parser.models import VerticalVisibility


class VerticalVisibilityParser:
    """Parses VVxxx tokens into a VerticalVisibility value object."""

    def matches(self, token: str) -> bool:
        """Return True if the token matches the VVxxx pattern. Logic pending."""
        raise NotImplementedError

    def parse(self, token: str) -> VerticalVisibility:
        """Parse a VVxxx token into a VerticalVisibility instance. Logic pending."""
        raise NotImplementedError
