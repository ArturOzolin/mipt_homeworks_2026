from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Any

from openai import OpenAI, OpenAIError

from core.config import AppConfig
from core.history import ApiMessage

TokenCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class LLMClient:
    api: OpenAI
    model: str
    temperature: float
    stream: bool

    @classmethod
    def from_config(cls, config: AppConfig) -> LLMClient:
        api = OpenAI(api_key=config.api_key, base_url=config.api_host)
        return cls(
            api=api,
            model=config.model,
            temperature=config.temperature,
            stream=config.stream,
        )

    def chat(self, messages: list[ApiMessage], on_token: TokenCallback | None = None) -> str:
        if self.stream:
            return self.chat_stream(messages, on_token)
        return self.chat_full(messages)

    def chat_full(self, messages: list[ApiMessage]) -> str:
        try:
            response = self.api.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=self.temperature,
            )
        except OpenAIError as exc:
            raise RuntimeError(f'Ошибка LLM: {exc}') from exc
        return response.choices[0].message.content or ''

    def chat_stream(
        self,
        messages: list[ApiMessage],
        on_token: TokenCallback | None,
    ) -> str:
        try:
            stream = self.api.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=self.temperature,
                stream=True,
            )
        except OpenAIError as exc:
            raise RuntimeError(f'Ошибка LLM: {exc}') from exc

        parts: list[str] = []
        try:
            for token in iter_tokens(stream):
                parts.append(token)
                if on_token is not None:
                    on_token(token)
        except OpenAIError as exc:
            raise RuntimeError(f'Ошибка LLM при стриминге: {exc}') from exc
        return ''.join(parts)


def iter_tokens(stream: Iterable[Any]) -> Iterator[str]:
    for event in stream:
        if not event.choices:
            continue
        delta = event.choices[0].delta
        if delta is None:
            continue
        content = getattr(delta, 'content', None)
        if content:
            yield content
