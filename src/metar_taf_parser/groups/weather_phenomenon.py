"""Parser for present-weather METAR/TAF groups."""

import re

from metar_taf_parser.enums import WeatherDescriptor, WeatherIntensity, WeatherPhenomenon
from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.models import PresentWeather

_DESCRIPTOR_CODES = "|".join(descriptor.value for descriptor in WeatherDescriptor)
_PHENOMENON_CODES = "|".join(phenomenon.value for phenomenon in WeatherPhenomenon)


class WeatherPhenomenonParser:
    """Parses weather tokens (e.g. +TSRA, -SHSN) into a PresentWeather value object."""

    # [intensity][descriptor][phenomenon...], e.g. `+` `TS` `RA`, `VC` `SH`, `-` `` `RASN`.
    _PATTERN = re.compile(
        rf"(?P<intensity>[-+]|VC)?"
        rf"(?P<descriptor>{_DESCRIPTOR_CODES})?"
        rf"(?P<phenomena>(?:{_PHENOMENON_CODES})*)"
    )

    def matches(self, token: str) -> bool:
        """Return True if the token is a present-weather group."""
        return self._match(token) is not None

    def parse(self, token: str) -> PresentWeather:
        """Parse a weather token into a PresentWeather instance.

        Raises:
            ParseError: If the token is not a present-weather group.
        """
        match = self._match(token)
        if match is None:
            raise ParseError(f"not a present-weather group: {token!r}")

        descriptor = match.group("descriptor")
        phenomena = match.group("phenomena")
        return PresentWeather(
            intensity=WeatherIntensity(match.group("intensity") or ""),
            descriptors=(WeatherDescriptor(descriptor),) if descriptor else (),
            phenomena=tuple(
                WeatherPhenomenon(phenomena[i : i + 2]) for i in range(0, len(phenomena), 2)
            ),
        )

    def _match(self, token: str) -> re.Match[str] | None:
        """Return the regex match, or None if the token isn't a weather group.

        Every part of the pattern is optional, so a bare intensity (`-`, `VC`)
        or an empty token would match; at least a descriptor or a phenomenon
        is required.
        """
        match = self._PATTERN.fullmatch(token)
        if match is None or not (match.group("descriptor") or match.group("phenomena")):
            return None
        return match
