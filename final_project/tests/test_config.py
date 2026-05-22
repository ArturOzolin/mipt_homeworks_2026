from __future__ import annotations

from pathlib import Path

import pytest

from core.config import ENV_KEYS, load_config


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_no_config_no_env_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        load_config(tmp_path / 'absent.yaml')


def test_env_only_loads(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('API_KEY', 'k')
    monkeypatch.setenv('API_HOST', 'http://localhost')
    monkeypatch.setenv('LIMIT_MESSAGE', '10')
    monkeypatch.setenv('TEMPERATURE', '0.4')
    config = load_config(tmp_path / 'absent.yaml')
    assert config.api_key == 'k'
    assert config.limit_message == 10
    assert config.temperature == 0.4


def test_yaml_only_loads(tmp_path: Path) -> None:
    cfg = tmp_path / 'config.yaml'
    cfg.write_text(
        'api_key: yk\n'
        'api_host: http://yaml\n'
        'limit_chars: 500\n'
        'system_prompt: be nice\n',
        encoding='utf-8',
    )
    config = load_config(cfg)
    assert config.api_key == 'yk'
    assert config.limit_chars == 500
    assert config.system_prompt == 'be nice'


def test_env_overrides_yaml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = tmp_path / 'config.yaml'
    cfg.write_text(
        'api_key: from_yaml\napi_host: http://yaml\nlimit_message: 5\n',
        encoding='utf-8',
    )
    monkeypatch.setenv('API_KEY', 'from_env')
    config = load_config(cfg)
    assert config.api_key == 'from_env'


def test_temperature_out_of_range(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('API_KEY', 'k')
    monkeypatch.setenv('API_HOST', 'h')
    monkeypatch.setenv('LIMIT_MESSAGE', '10')
    monkeypatch.setenv('TEMPERATURE', '1.5')
    with pytest.raises(ValueError):
        load_config(tmp_path / 'absent.yaml')


def test_no_limits_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('API_KEY', 'k')
    monkeypatch.setenv('API_HOST', 'h')
    with pytest.raises(ValueError):
        load_config(tmp_path / 'absent.yaml')


def test_negative_limit_message(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('API_KEY', 'k')
    monkeypatch.setenv('API_HOST', 'h')
    monkeypatch.setenv('LIMIT_MESSAGE', '-5')
    with pytest.raises(ValueError):
        load_config(tmp_path / 'absent.yaml')


def test_invalid_yaml(tmp_path: Path) -> None:
    cfg = tmp_path / 'bad.yaml'
    cfg.write_text('not: a: dict: structure', encoding='utf-8')
    with pytest.raises(ValueError):
        load_config(cfg)
