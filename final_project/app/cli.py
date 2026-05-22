from __future__ import annotations

from typing import Protocol

from core.config import AppConfig, load_config
from core.history import ApiMessage, History
from llm.client import LLMClient
from tools.chunking import ChunkOptions, chunk_text, is_chunk_command, parse_chunk_command
from tools.files import inject_file_contents, read_text_file, resolve_path

PROMPT = '>>> '
QUIT_COMMAND = '\\q'
RESET_COMMAND = '/reset'
NEXT_CHUNK_HINT = '(Enter — следующий чанк, \\q — выйти из режима)'


class ChatClient(Protocol):
    @property
    def stream(self) -> bool: ...

    def chat(self, messages: list[ApiMessage], on_token=None) -> str: ...  # type: ignore[no-untyped-def]


def main() -> int:
    try:
        config = load_config()
    except ValueError as exc:
        print(f'Ошибка конфигурации: {exc}')
        return 1

    client = LLMClient.from_config(config)
    history = History(config.system_prompt, config.limit_message, config.limit_chars)
    print('GigaVibeMiptCode — введи сообщение, /reset для сброса, \\q для выхода.')

    while True:
        try:
            raw = input(PROMPT)
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            continue

        text = raw.strip()
        if not text:
            continue
        if text == QUIT_COMMAND:
            return 0
        if text == RESET_COMMAND:
            history.clear()
            clear_screen()
            continue
        if is_chunk_command(text):
            run_chunk_mode(text, client, config)
            continue

        run_chat_turn(raw, history, client)


def run_chat_turn(raw_user: str, history: History, client: ChatClient) -> None:
    prepared, errors = inject_file_contents(raw_user)
    for error in errors:
        print(f'Файл: {error}')

    history.add_user(prepared)
    messages = history.build_for_request()

    answer = safe_chat(client, messages)
    if answer is None:
        return
    history.add_assistant(answer)


def safe_chat(client: ChatClient, messages: list[ApiMessage]) -> str | None:
    try:
        if client.stream:
            answer = client.chat(messages, on_token=print_token)
            print()
            return answer
        answer = client.chat(messages)
        print(answer)
        return answer
    except KeyboardInterrupt:
        print('\nЗапрос прерван пользователем.')
        return None
    except RuntimeError as exc:
        print(exc)
        return None


def print_token(token: str) -> None:
    print(token, end='', flush=True)


def run_chunk_mode(command: str, client: ChatClient, config: AppConfig) -> None:
    try:
        options = parse_chunk_command(command)
    except ValueError as exc:
        print(exc)
        return

    print('Введите путь до файла:')
    try:
        file_path_input = input(PROMPT).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if file_path_input == QUIT_COMMAND or not file_path_input:
        return

    try:
        text = read_text_file(resolve_path(file_path_input))
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return

    print('Что нужно сделать для каждого фрагмента (User Prompt)?')
    try:
        user_prompt = input(PROMPT).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if user_prompt == QUIT_COMMAND:
        return

    chunks = chunk_text(text, options)
    if not chunks:
        print('Нет чанков для обработки.')
        return

    print(f'Принято. Начинаю обработку ({len(chunks)} чанков).')
    process_chunks(chunks, user_prompt, options, client, config)
    print('Обработка файла завершена.')


def process_chunks(
    chunks: list[str],
    user_prompt: str,
    options: ChunkOptions,
    client: ChatClient,
    config: AppConfig,
) -> None:
    total = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        prompt = f'{user_prompt}\n\n{chunk}' if user_prompt else chunk
        message: ApiMessage = {'role': 'user', 'content': prompt}
        messages: list[ApiMessage] = []
        if config.system_prompt:
            messages.append({'role': 'system', 'content': config.system_prompt})
        messages.append(message)

        answer = safe_chat(client, messages)
        if answer is None:
            return
        if options.auto or index == total:
            continue

        print(NEXT_CHUNK_HINT)
        try:
            wait = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if wait == QUIT_COMMAND:
            return


def clear_screen() -> None:
    print('\n' * 50)
