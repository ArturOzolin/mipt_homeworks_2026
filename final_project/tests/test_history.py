from __future__ import annotations

from core.history import History, Role, truncate_left


def test_truncate_left_under_limit() -> None:
    assert truncate_left('hello', 10) == 'hello'


def test_truncate_left_over_limit() -> None:
    assert truncate_left('abcdef', 3) == 'def'


def test_truncate_left_none() -> None:
    assert truncate_left('abc', None) == 'abc'


def test_limit_messages_trims_oldest() -> None:
    h = History(system_prompt=None, limit_message=3, limit_chars=None)
    h.add_user('u1')
    h.add_assistant('a1')
    h.add_user('u2')
    h.add_assistant('a2')
    contents = [m.content for m in h]
    assert contents == ['a1', 'u2', 'a2']


def test_limit_chars_drops_old() -> None:
    h = History(system_prompt=None, limit_message=None, limit_chars=10)
    h.add_user('a' * 4)
    h.add_user('b' * 4)
    h.add_user('c' * 4)
    remaining = ''.join(m.content for m in h)
    assert len(remaining) <= 10
    assert remaining.endswith('c' * 4)


def test_single_long_message_left_truncated() -> None:
    h = History(system_prompt=None, limit_message=None, limit_chars=5)
    h.add_user('1234567890')
    msgs = list(h)
    assert len(msgs) == 1
    assert msgs[0].content == '67890'


def test_build_for_request_starts_with_system() -> None:
    h = History(system_prompt='SYS', limit_message=10, limit_chars=None)
    h.add_user('hi')
    msgs = h.build_for_request()
    assert msgs[0] == {'role': 'system', 'content': 'SYS'}
    assert msgs[-1] == {'role': 'user', 'content': 'hi'}


def test_build_for_request_without_system() -> None:
    h = History(system_prompt=None, limit_message=10, limit_chars=None)
    h.add_user('hi')
    msgs = h.build_for_request()
    assert msgs == [{'role': 'user', 'content': 'hi'}]


def test_clear() -> None:
    h = History('SYS', limit_message=10, limit_chars=None)
    h.add_user('x')
    h.clear()
    assert len(h) == 0


def test_role_values() -> None:
    assert Role.USER.value == 'user'
    assert Role.ASSISTANT.value == 'assistant'
    assert Role.SYSTEM.value == 'system'
