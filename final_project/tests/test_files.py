from __future__ import annotations

from pathlib import Path

import pytest

from tools.files import inject_file_contents, read_text_file, resolve_path


def test_resolve_path_absolute(tmp_path: Path) -> None:
    p = tmp_path / 'x.txt'
    p.write_text('hi')
    assert resolve_path(str(p)) == p


def test_resolve_path_relative_uses_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert resolve_path('a.txt') == (tmp_path / 'a.txt').resolve()


def test_read_text_file_ok(tmp_path: Path) -> None:
    p = tmp_path / 'a.txt'
    p.write_text('hello', encoding='utf-8')
    assert read_text_file(p) == 'hello'


def test_read_text_file_too_big(tmp_path: Path) -> None:
    p = tmp_path / 'big.txt'
    p.write_bytes(b'x' * 100)
    with pytest.raises(ValueError):
        read_text_file(p, max_bytes=10)


def test_read_text_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_text_file(tmp_path / 'missing.txt')


def test_inject_replaces_reference(tmp_path: Path) -> None:
    p = tmp_path / 'code.py'
    p.write_text('print(1)', encoding='utf-8')
    text, errors = inject_file_contents(f'Помоги: @::{p}::')
    assert 'print(1)' in text
    assert errors == []


def test_inject_collects_errors_when_missing(tmp_path: Path) -> None:
    text, errors = inject_file_contents(f'Что в @::{tmp_path / "nope.txt"}::?')
    assert errors
    assert 'nope.txt' in errors[0]


def test_inject_no_pattern_passthrough() -> None:
    text, errors = inject_file_contents('just hello')
    assert text == 'just hello'
    assert errors == []


def test_inject_too_big_file(tmp_path: Path) -> None:
    p = tmp_path / 'big.txt'
    p.write_bytes(b'x' * 100)
    _, errors = inject_file_contents(f'@::{p}::', max_bytes=10)
    assert errors
    assert 'слишком большой' in errors[0]
