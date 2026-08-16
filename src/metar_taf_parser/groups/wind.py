"""Parser for the wind METAR/TAF group."""

from metar_taf_parser.models import Wind


class WindParser:
    """Parses wind tokens (e.g. 24010G20KT) into a Wind value object."""

    def matches(self, token: str) -> bool:
        """Return True if the token matches the wind group pattern. Logic pending."""
        raise NotImplementedError

    def parse(self, token: str) -> Wind:
        """Parse a wind token into a Wind instance. Logic pending."""
        raise NotImplementedError
