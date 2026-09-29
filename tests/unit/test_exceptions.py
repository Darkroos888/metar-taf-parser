"""Structural tests for the exception hierarchy.

Every error raised by the library derives from `ParseError`, so a caller can
catch any parsing failure with a single `except ParseError`.
"""

import pytest

from metar_taf_parser.exceptions import InvalidReportError, ParseError, UnknownTokenError


class TestExceptionHierarchy:
    """Jerarquía de excepciones de la librería."""

    def test_parse_error_is_an_exception(self):
        """ParseError es la raíz y deriva de Exception."""
        assert issubclass(ParseError, Exception)

    @pytest.mark.parametrize("exc_cls", [UnknownTokenError, InvalidReportError])
    def test_specific_errors_derive_from_parse_error(self, exc_cls):
        """Los errores concretos son subclases de ParseError."""
        assert issubclass(exc_cls, ParseError)

    @pytest.mark.parametrize("exc_cls", [UnknownTokenError, InvalidReportError])
    def test_specific_errors_can_be_caught_as_parse_error(self, exc_cls):
        """Un `except ParseError` captura cualquier error concreto."""
        with pytest.raises(ParseError):
            raise exc_cls("boom")

    @pytest.mark.parametrize("exc_cls", [ParseError, UnknownTokenError, InvalidReportError])
    def test_preserves_message(self, exc_cls):
        """El mensaje pasado al constructor se conserva en str()."""
        assert str(exc_cls("token inválido: XYZ")) == "token inválido: XYZ"

    def test_specific_errors_are_distinct(self):
        """UnknownTokenError e InvalidReportError no se capturan entre sí."""
        assert not issubclass(UnknownTokenError, InvalidReportError)
        assert not issubclass(InvalidReportError, UnknownTokenError)
