"""Structural contract of the report-parser layer (no parsing behavior)."""

import pytest

from metar_taf_parser.groups.base import GroupParser
from metar_taf_parser.parsers.base import AbstractReportParser
from metar_taf_parser.parsers.metar import MetarParser
from metar_taf_parser.parsers.taf import TafParser

REPORT_PARSERS = [MetarParser, TafParser]


def test_abstract_report_parser_cannot_be_instantiated():
    """AbstractReportParser es abstracta: sin `_assemble()` no se puede instanciar."""
    with pytest.raises(TypeError):
        AbstractReportParser([])


@pytest.mark.parametrize("parser_cls", REPORT_PARSERS)
class TestReportParserContract:
    """Contrato compartido por MetarParser y TafParser."""

    def test_is_a_report_parser(self, parser_cls):
        """Hereda de AbstractReportParser (Template Method)."""
        assert issubclass(parser_cls, AbstractReportParser)

    def test_can_be_instantiated_without_arguments(self, parser_cls):
        """Implementa `_assemble()` y registra sus propios group parsers."""
        parser_cls()

    def test_registers_every_group_parser(self, parser_cls):
        """Registra los 7 group parsers, todos cumpliendo el Protocol."""
        group_parsers = parser_cls()._group_parsers
        assert len(group_parsers) == 7
        assert all(isinstance(p, GroupParser) for p in group_parsers)
