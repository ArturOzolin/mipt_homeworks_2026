from __future__ import annotations

import pytest

from tools.chunking import (
    ChunkMode,
    ChunkOptions,
    chunk_text,
    is_chunk_command,
    parse_chunk_command,
)


def test_is_chunk_command() -> None:
    assert is_chunk_command('/file_chunk')
    assert is_chunk_command('/filechunk paragraph=2')
    assert not is_chunk_command('hello')


def test_parse_default_paragraph() -> None:
    opts = parse_chunk_command('/file_chunk')
    assert opts.mode is ChunkMode.PARAGRAPH
    assert opts.paragraph_count == 1
    assert not opts.auto


def test_parse_paragraph_count() -> None:
    opts = parse_chunk_command('/file_chunk paragraph=3 -y')
    assert opts.mode is ChunkMode.PARAGRAPH
    assert opts.paragraph_count == 3
    assert opts.auto


def test_parse_length() -> None:
    opts = parse_chunk_command('/file_chunk len=150')
    assert opts.mode is ChunkMode.LENGTH
    assert opts.length == 150


def test_parse_rejects_mixed_modes() -> None:
    with pytest.raises(ValueError):
        parse_chunk_command('/file_chunk paragraph=2 len=100')


def test_parse_unknown_option() -> None:
    with pytest.raises(ValueError):
        parse_chunk_command('/file_chunk extra=1')


def test_parse_non_positive() -> None:
    with pytest.raises(ValueError):
        parse_chunk_command('/file_chunk paragraph=0')


def test_chunk_text_by_length() -> None:
    text = 'abcdefghij'
    chunks = chunk_text(text, ChunkOptions(mode=ChunkMode.LENGTH, length=3))
    assert chunks == ['abc', 'def', 'ghi', 'j']


def test_chunk_text_by_paragraph() -> None:
    text = 'one\n\ntwo\n\nthree\n\nfour'
    chunks = chunk_text(text, ChunkOptions(mode=ChunkMode.PARAGRAPH, paragraph_count=2))
    assert chunks == ['one\n\ntwo', 'three\n\nfour']


def test_chunk_text_single_paragraph_default() -> None:
    text = 'one\n\ntwo\n\nthree'
    chunks = chunk_text(text, ChunkOptions(mode=ChunkMode.PARAGRAPH, paragraph_count=1))
    assert chunks == ['one', 'two', 'three']


def test_chunk_empty_text_returns_empty() -> None:
    assert chunk_text('   ', ChunkOptions(mode=ChunkMode.PARAGRAPH)) == []
