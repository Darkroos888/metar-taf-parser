"""Exceptions raised while parsing METAR/TAF reports."""


class ParseError(Exception):
    """Base class for every error raised while parsing a report."""


class UnknownTokenError(ParseError):
    """A token was not accepted by any group parser."""


class InvalidReportError(ParseError):
    """A report is structurally invalid (e.g. missing a mandatory group)."""
