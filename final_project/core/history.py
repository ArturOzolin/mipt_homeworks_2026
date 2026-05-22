from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


class Role(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


class ApiMessage(TypedDict):
    role: str
    content: str


@dataclass(slots=True)
class Message:
    role: Role
    content: str

    def to_api(self) -> ApiMessage:
        return {'role': self.role.value, 'content': self.content}


def truncate_left(content: str, limit_chars: int | None) -> str:
    if limit_chars is None or len(content) <= limit_chars:
        return content
    return content[-limit_chars:]


class History:
    def __init__(
        self,
        system_prompt: str | None,
        limit_message: int | None,
        limit_chars: int | None,
    ) -> None:
        self.system_prompt = system_prompt
        self.limit_message = limit_message
        self.limit_chars = limit_chars
        self.messages: list[Message] = []

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self) -> Iterator[Message]:
        return iter(self.messages)

    def clear(self) -> None:
        self.messages.clear()

    def add_user(self, content: str) -> None:
        self.messages.append(Message(Role.USER, truncate_left(content, self.limit_chars)))
        self.enforce_limits()

    def add_assistant(self, content: str) -> None:
        self.messages.append(Message(Role.ASSISTANT, truncate_left(content, self.limit_chars)))
        self.enforce_limits()

    def build_for_request(self) -> list[ApiMessage]:
        messages: list[Message] = []
        if self.system_prompt:
            messages.append(Message(Role.SYSTEM, self.system_prompt))
        messages.extend(self.messages)
        return [m.to_api() for m in messages]

    def enforce_limits(self) -> None:
        if self.limit_message is not None:
            while len(self.messages) > self.limit_message:
                self.messages.pop(0)
        if self.limit_chars is not None:
            total = sum(len(m.content) for m in self.messages)
            while self.messages and total > self.limit_chars:
                removed = self.messages.pop(0)
                total -= len(removed.content)
