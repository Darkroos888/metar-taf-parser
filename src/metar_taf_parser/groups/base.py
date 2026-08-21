"""Shared contract implemented by every METAR/TAF group parser."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class GroupParser(Protocol):
    """Common contract every group parsers must satisfy."""

    def matches(self, token: str) -> bool:
        """Return True if this parser recognizes the given token."""
        ...

    def parse(self, token: str) -> object:
        """Parse the token into its corresponding value object."""
        ...
