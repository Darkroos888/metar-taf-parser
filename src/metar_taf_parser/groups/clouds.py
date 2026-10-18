"""Parser for cloud layer METAR/TAF groups."""

import re

from metar_taf_parser.enums import CloudAmount
from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.models import CloudLayer


class CloudParser:
    """Parses cloud tokens (e.g. FEW020, BKN250CB) into a CloudLayer value object."""

    _PATTERN = re.compile(
        r"(?P<amount>FEW|SCT|BKN|OVC)(?P<height>\d{3})(?P<convective>CB|TCU)?"
        r"|(?P<clear>SKC|CLR|NSC)"
    )

    def matches(self, token: str) -> bool:
        """Return True if the token matches the cloud group pattern. Logic pending."""
        return self._PATTERN.fullmatch(token) is not None

    def parse(self, token: str) -> CloudLayer:
        """Parse a cloud token into a CloudLayer instance. Logic pending."""
        match = self._PATTERN.fullmatch(token)
        if match is None:
            raise ParseError(f"not a cloud group: {token!r}")
        clear = match.group("clear")
        if clear is not None:
            return CloudLayer(amount=CloudAmount(clear),height_ft=0)
        return CloudLayer(
            amount = CloudAmount(match.group("amount")),
            height_ft = int(match.group("height")) * 100,
            convective_type = match.group("convective"),
        )
