from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ENV_KEYS = (
    'API_KEY',
    'API_HOST',
    'MODEL',
    'TEMPERATURE',
    'LIMIT_MESSAGE',
    'LIMIT_CHARS',
    'STREAM',
)

DEFAULT_MODEL = 'gemma3:270m'
DEFAULT_CONFIG_PATH = Path('config.yaml')


@dataclass(frozen=True, slots=True)
class AppConfig:
    api_key: str
    api_host: str
    model: str
    temperature: float
    limit_message: int | None
    limit_chars: int | None
    system_prompt: str | None
    stream: bool


def load_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or DEFAULT_CONFIG_PATH
    yaml_data = read_yaml(path) if path.is_file() else {}
    env_present = any(os.environ.get(key) is not None for key in ENV_KEYS)

    if not yaml_data and not env_present:
        raise ValueError(
            'Не заданы ни переменные окружения, ни config.yaml. '
            'Создайте config.yaml или экспортируйте API_KEY и API_HOST.'
        )

    api_key = require_str('API_KEY', 'api_key', yaml_data)
    api_host = require_str('API_HOST', 'api_host', yaml_data)
    model = optional_str('MODEL', 'model', yaml_data) or DEFAULT_MODEL

    temperature = optional_float('TEMPERATURE', 'temperature', yaml_data, default=0.7)
    limit_message = optional_int('LIMIT_MESSAGE', 'limit_message', yaml_data)
    limit_chars = optional_int('LIMIT_CHARS', 'limit_chars', yaml_data)
    stream = optional_bool('STREAM', 'stream', yaml_data, default=False)
    system_prompt = optional_str(None, 'system_prompt', yaml_data)

    validate_config(temperature, limit_message, limit_chars, model)

    return AppConfig(
        api_key=api_key,
        api_host=api_host,
        model=model,
        temperature=temperature,
        limit_message=limit_message,
        limit_chars=limit_chars,
        system_prompt=system_prompt,
        stream=stream,
    )


def validate_config(
    temperature: float,
    limit_message: int | None,
    limit_chars: int | None,
    model: str,
) -> None:
    if temperature < 0 or temperature > 1:
        raise ValueError('temperature должен быть числом в диапазоне [0, 1].')
    if limit_message is not None and limit_message <= 0:
        raise ValueError('limit_message должен быть положительным.')
    if limit_chars is not None and limit_chars <= 0:
        raise ValueError('limit_chars должен быть положительным.')
    if limit_message is None and limit_chars is None:
        raise ValueError('Задайте хотя бы один лимит: limit_message или limit_chars.')
    if not model.strip():
        raise ValueError('model не может быть пустым.')


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as exc:
        raise ValueError(f'Не удалось прочитать {path}: {exc}') from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f'Некорректный YAML в {path}: {exc}') from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f'В {path} ожидается словарь в корне.')
    return data


def get_raw_value(
    env_key: str | None,
    yaml_key: str,
    yaml_data: dict[str, Any],
) -> object | None:
    if env_key is not None:
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
    return yaml_data.get(yaml_key)


def optional_str(env_key: str | None, yaml_key: str, yaml_data: dict[str, Any]) -> str | None:
    value = get_raw_value(env_key, yaml_key, yaml_data)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f'{yaml_key} должен быть строкой.')
    text = value.strip()
    return text or None


def require_str(env_key: str, yaml_key: str, yaml_data: dict[str, Any]) -> str:
    value = optional_str(env_key, yaml_key, yaml_data)
    if value is None:
        raise ValueError(f'Не задан обязательный параметр {yaml_key}.')
    return value


def optional_int(env_key: str, yaml_key: str, yaml_data: dict[str, Any]) -> int | None:
    value = get_raw_value(env_key, yaml_key, yaml_data)
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f'{yaml_key} должен быть целым числом.')
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError as exc:
            raise ValueError(f'{yaml_key} должен быть целым числом.') from exc
    raise ValueError(f'{yaml_key} должен быть целым числом.')


def optional_float(
    env_key: str,
    yaml_key: str,
    yaml_data: dict[str, Any],
    default: float,
) -> float:
    value = get_raw_value(env_key, yaml_key, yaml_data)
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError(f'{yaml_key} должен быть числом.')
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f'{yaml_key} должен быть числом.') from exc
    raise ValueError(f'{yaml_key} должен быть числом.')


def optional_bool(
    env_key: str,
    yaml_key: str,
    yaml_data: dict[str, Any],
    default: bool,
) -> bool:
    value = get_raw_value(env_key, yaml_key, yaml_data)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {'1', 'true', 'yes', 'y', 'on'}:
            return True
        if text in {'0', 'false', 'no', 'n', 'off'}:
            return False
    raise ValueError(f'{yaml_key} должен быть булевым значением.')
