from typing import Protocol, runtime_checkable


@runtime_checkable
class GroupParser(Protocol):
    """Common contract every group parsers must satisfy."""

    def matches(self, token: str) -> bool: ...
    def parse(self, token: str) -> object: ...
