from __future__ import annotations

import shlex
from dataclasses import dataclass
from enum import Enum

CHUNK_COMMANDS = ('/file_chunk', '/filechunk')


class ChunkMode(str, Enum):
    PARAGRAPH = 'paragraph'
    LENGTH = 'length'


@dataclass(frozen=True, slots=True)
class ChunkOptions:
    mode: ChunkMode
    paragraph_count: int = 1
    length: int | None = None
    auto: bool = False


def is_chunk_command(text: str) -> bool:
    head = text.strip().split(maxsplit=1)
    return bool(head) and head[0] in CHUNK_COMMANDS


def parse_chunk_command(command: str) -> ChunkOptions:
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f'Не удалось разобрать команду: {exc}') from exc
    if not tokens or tokens[0] not in CHUNK_COMMANDS:
        raise ValueError('Команда должна начинаться с /file_chunk.')

    paragraph_count = 1
    length: int | None = None
    auto = False
    mode_chosen: ChunkMode | None = None

    for token in tokens[1:]:
        if token in {'-y', '--yes'}:
            auto = True
            continue
        if token.startswith('paragraph='):
            if mode_chosen is ChunkMode.LENGTH:
                raise ValueError('Нельзя сочетать paragraph и len.')
            paragraph_count = positive_int(token.split('=', 1)[1], 'paragraph')
            mode_chosen = ChunkMode.PARAGRAPH
            continue
        if token.startswith('len='):
            if mode_chosen is ChunkMode.PARAGRAPH:
                raise ValueError('Нельзя сочетать paragraph и len.')
            length = positive_int(token.split('=', 1)[1], 'len')
            mode_chosen = ChunkMode.LENGTH
            continue
        raise ValueError(f'Неизвестная опция: {token}')

    if mode_chosen is ChunkMode.LENGTH:
        return ChunkOptions(mode=ChunkMode.LENGTH, length=length, auto=auto)
    return ChunkOptions(mode=ChunkMode.PARAGRAPH, paragraph_count=paragraph_count, auto=auto)


def chunk_text(text: str, options: ChunkOptions) -> list[str]:
    if options.mode is ChunkMode.LENGTH:
        length = options.length or 0
        if length <= 0:
            return []
        return [text[i:i + length] for i in range(0, len(text), length)]

    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return []
    step = max(1, options.paragraph_count)
    return [
        '\n\n'.join(paragraphs[i:i + step])
        for i in range(0, len(paragraphs), step)
    ]


def split_paragraphs(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    paragraphs: list[str] = []
    current: list[str] = []
    for line in stripped.splitlines():
        if line.strip() == '':
            if current:
                paragraphs.append('\n'.join(current).strip())
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append('\n'.join(current).strip())
    return [p for p in paragraphs if p]


def positive_int(raw: str, name: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f'{name} должен быть целым числом.') from exc
    if value <= 0:
        raise ValueError(f'{name} должен быть положительным.')
    return value
