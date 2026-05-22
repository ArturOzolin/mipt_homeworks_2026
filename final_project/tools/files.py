from __future__ import annotations

from pathlib import Path

MAX_FILE_BYTES = 5 * 1024 * 1024
OPEN_MARKER = '@::'
CLOSE_MARKER = '::'


def resolve_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def read_text_file(path: Path, max_bytes: int = MAX_FILE_BYTES) -> str:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise FileNotFoundError(f'Не удалось получить размер файла: {path}') from exc
    if size > max_bytes:
        raise ValueError(f'Файл слишком большой ({size} байт, лимит {max_bytes})')
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        raise FileNotFoundError(f'Не удалось прочитать файл: {path}') from exc


def inject_file_contents(text: str, max_bytes: int = MAX_FILE_BYTES) -> tuple[str, list[str]]:
    errors: list[str] = []
    parts: list[str] = []
    cursor = 0
    while cursor < len(text):
        start = text.find(OPEN_MARKER, cursor)
        if start == -1:
            parts.append(text[cursor:])
            break
        end = text.find(CLOSE_MARKER, start + len(OPEN_MARKER))
        if end == -1:
            parts.append(text[cursor:])
            break

        parts.append(text[cursor:start])
        raw_path = text[start + len(OPEN_MARKER):end].strip()
        content, error = load_file_for_reference(raw_path, max_bytes)
        if error is not None:
            errors.append(error)
        elif content is not None:
            parts.append(f'\n{content}')
        cursor = end + len(CLOSE_MARKER)

    return ''.join(parts), errors


def load_file_for_reference(raw_path: str, max_bytes: int) -> tuple[str | None, str | None]:
    if not raw_path:
        return None, 'Пустая ссылка на файл в @::::'
    path = resolve_path(raw_path)
    if not path.exists():
        return None, f'Файл не найден: {raw_path}'
    if not path.is_file():
        return None, f'Это не файл: {raw_path}'
    try:
        return read_text_file(path, max_bytes), None
    except (FileNotFoundError, ValueError) as exc:
        return None, str(exc)
