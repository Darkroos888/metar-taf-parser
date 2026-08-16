"""Parser for cloud layer METAR/TAF groups."""

from metar_taf_parser.models import CloudLayer


class CloudParser:
    """Parses cloud tokens (e.g. FEW020, BKN250CB) into a CloudLayer value object."""

    def matches(self, token: str) -> bool:
        """Return True if the token matches the cloud group pattern. Logic pending."""
        raise NotImplementedError

    def parse(self, token: str) -> CloudLayer:
        """Parse a cloud token into a CloudLayer instance. Logic pending."""
        raise NotImplementedError
