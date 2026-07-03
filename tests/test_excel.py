"""Testes dos parsers de célula — a lógica onde um bug corrompe dado financeiro."""

from datetime import datetime

import pytest

from automacao.excel import parse_data, parse_documento, parse_numero


@pytest.mark.parametrize("entrada", [None, ""])
def test_parse_data_vazio(entrada):
    assert parse_data(entrada) is None


def test_parse_data_string_br():
    assert parse_data("25/12/2026") == datetime(2026, 12, 25)


def test_parse_data_datetime_passa_direto():
    d = datetime(2026, 1, 2, 3, 4)
    assert parse_data(d) is d


def test_parse_data_com_espacos():
    assert parse_data("  01/02/2026 ") == datetime(2026, 2, 1)


def test_parse_data_invalida_levanta():
    with pytest.raises(ValueError):
        parse_data("2026-12-25")


@pytest.mark.parametrize("entrada", [None, ""])
def test_parse_numero_vazio(entrada):
    assert parse_numero(entrada) is None


def test_parse_numero_formato_br():
    assert parse_numero("1.234.567,89") == 1234567.89


def test_parse_numero_sem_milhar():
    assert parse_numero("12,50") == 12.5


def test_parse_numero_ja_numerico():
    assert parse_numero(10) == 10
    assert parse_numero(3.5) == 3.5


@pytest.mark.parametrize("entrada", ["", "-"])
def test_parse_numero_placeholder_vira_none(entrada):
    assert parse_numero(entrada) is None


@pytest.mark.parametrize("entrada", [None, ""])
def test_parse_documento_vazio_vira_zero(entrada):
    assert parse_documento(entrada) == 0


def test_parse_documento_string_numerica():
    assert parse_documento("  123 ") == 123


def test_parse_documento_float_trunca():
    assert parse_documento(45.9) == 45


def test_parse_documento_nao_numerico_preserva():
    assert parse_documento("NF-001") == "NF-001"
