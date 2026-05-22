from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from app import cli
from core.config import AppConfig
from core.history import ApiMessage, History


class FakeClient:
    def __init__(self, replies: Iterable[str], stream: bool = False) -> None:
        self.replies = list(replies)
        self.stream = stream
        self.calls: list[list[ApiMessage]] = []

    def chat(self, messages: list[ApiMessage], on_token: Any = None) -> str:
        self.calls.append(list(messages))
        if not self.replies:
            raise RuntimeError('закончились заготовленные ответы')
        reply = self.replies.pop(0)
        if self.stream and on_token is not None:
            for ch in reply:
                on_token(ch)
        return reply


def make_config(**overrides: Any) -> AppConfig:
    base: dict[str, Any] = {
        'api_key': 'k',
        'api_host': 'http://x',
        'model': 'm',
        'temperature': 0.5,
        'limit_message': 10,
        'limit_chars': None,
        'system_prompt': None,
        'stream': False,
    }
    base.update(overrides)
    return AppConfig(**base)


def test_chat_turn_appends_assistant() -> None:
    history = History(system_prompt=None, limit_message=10, limit_chars=None)
    client = FakeClient(replies=['hi back'])
    cli.run_chat_turn('hi', history, client)
    contents = [m.content for m in history]
    assert contents == ['hi', 'hi back']


def test_chat_turn_handles_llm_error(capsys: pytest.CaptureFixture[str]) -> None:
    class Broken:
        stream = False

        def chat(self, messages: list[ApiMessage], on_token: Any = None) -> str:
            raise RuntimeError('сервер упал')

    history = History(system_prompt=None, limit_message=10, limit_chars=None)
    cli.run_chat_turn('hi', history, Broken())
    assert 'сервер упал' in capsys.readouterr().out
    contents = [m.content for m in history]
    assert contents == ['hi']


def test_chat_turn_keyboard_interrupt(capsys: pytest.CaptureFixture[str]) -> None:
    class Boom:
        stream = False

        def chat(self, messages: list[ApiMessage], on_token: Any = None) -> str:
            raise KeyboardInterrupt

    history = History(system_prompt=None, limit_message=10, limit_chars=None)
    cli.run_chat_turn('hi', history, Boom())
    assert 'прерван' in capsys.readouterr().out


def test_chat_turn_streams_tokens(capsys: pytest.CaptureFixture[str]) -> None:
    history = History(system_prompt=None, limit_message=10, limit_chars=None)
    client = FakeClient(replies=['abc'], stream=True)
    cli.run_chat_turn('hi', history, client)
    out = capsys.readouterr().out
    assert 'abc' in out


def test_run_chunk_mode_processes_paragraphs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_path = tmp_path / 'book.txt'
    file_path.write_text('one\n\ntwo\n\nthree', encoding='utf-8')

    inputs = iter([str(file_path), 'summarize'])

    def fake_input(prompt: str = '') -> str:
        return next(inputs)

    monkeypatch.setattr('builtins.input', fake_input)
    config = make_config()
    client = FakeClient(replies=['s1', 's2', 's3'])
    cli.run_chunk_mode('/file_chunk -y', client, config)
    assert len(client.calls) == 3
    assert 'завершена' in capsys.readouterr().out


def test_run_returns_on_quit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('API_KEY', 'k')
    monkeypatch.setenv('API_HOST', 'http://localhost')
    monkeypatch.setenv('LIMIT_MESSAGE', '5')
    monkeypatch.chdir(tmp_path)

    inputs = iter(['\\q'])
    monkeypatch.setattr('builtins.input', lambda _prompt='': next(inputs))

    class DummyClient:
        stream = False

        @classmethod
        def from_config(cls, config: AppConfig) -> 'DummyClient':
            return cls()

        def chat(self, messages: list[ApiMessage], on_token: Any = None) -> str:
            return ''

    monkeypatch.setattr(cli, 'LLMClient', DummyClient)
    assert cli.main() == 0


def test_run_reset_clears_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('API_KEY', 'k')
    monkeypatch.setenv('API_HOST', 'http://localhost')
    monkeypatch.setenv('LIMIT_MESSAGE', '5')
    monkeypatch.chdir(tmp_path)

    inputs = iter(['hi', '/reset', '\\q'])
    monkeypatch.setattr('builtins.input', lambda _prompt='': next(inputs))
    monkeypatch.setattr(cli, 'clear_screen', lambda: None)

    class DummyClient:
        stream = False

        @classmethod
        def from_config(cls, config: AppConfig) -> 'DummyClient':
            return cls()

        def chat(self, messages: list[ApiMessage], on_token: Any = None) -> str:
            return 'ok'

    monkeypatch.setattr(cli, 'LLMClient', DummyClient)
    assert cli.main() == 0
