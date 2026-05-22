# GigaVibeMiptCode

Консольный чат с LLM по OpenAI-совместимому API.

## Установка

```bash
pip install openai pyyaml pytest pytest-cov
```

Запустить локальную модель через Ollama:

```bash
ollama pull gemma3:270m
ollama serve
```

## Настройка

Скопируй пример конфига и подставь свои значения:

```bash
cp config.yaml.example config.yaml
```

Можно задавать настройки и переменными окружения

## Запуск

```bash
python main.py
```

## Команды в чате

- `/reset` — очистить историю и экран
- `/file_chunk paragraph=2 -y` — обработать файл по чанкам
- `@::/path/to/file.txt::` — вставить содержимое файла в запрос
- `\q` — выйти

## Тесты

```bash
pytest tests/ --cov=app --cov=core --cov=llm --cov=tools --cov-report=html
```
