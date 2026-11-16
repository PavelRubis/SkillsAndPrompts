---
name: "youtube-analyzer"
description: "YouTube через Gemini: транскрибация + саммари, сохранение в Notion."
version: 0.2.0
author: Hermes Agent
platforms: [linux]
---

# YouTube Analyzer

Анализирует YouTube-видео через Google Gemini (через OpenRouter API) и сохраняет результат в Notion.

## Триггер

Кинуть ссылку на YouTube с опциональными ключевыми словами:

- `https://youtube.com/watch?v=...` — полный анализ (транскрибация + саммари)
- `https://youtube.com/watch?v=... транскрибация` — только транскрибация
- `https://youtube.com/watch?v=... саммари` — только саммари

Слова могут быть в любом месте сообщения (до или после ссылки).

## Workflow

### 1. Получить длительность видео

**Primary:** yt-dlp по абсолютному пути `~/.hermes/tools/bin/yt-dlp`

```bash
~/.hermes/tools/bin/yt-dlp --print duration_string "URL"
```

Если бинарника нет — поставить:

```bash
mkdir -p ~/.hermes/tools/bin
curl -sL "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux" -o ~/.hermes/tools/bin/yt-dlp
chmod +x ~/.hermes/tools/bin/yt-dlp
```

(В PATH его нет и он не сохраняется между вызовами — всегда вызывать по полному пути.)

**Fallback:** YouTube oEmbed

```
https://www.youtube.com/oembed?url=URL&format=json
```

через `web_extract`; длительность в oEmbed есть не всегда.

⚠️ yt-dlp может писать в stderr предупреждение `No supported JavaScript runtime could be found` — это **не фатально**, метаданные всё равно печатаются в stdout. Не считать ошибкой. Результат забирать через `tail -1` (в stdout бывает лишний шум).

### 2. Выбрать модель

- Длительность **≤ 30 минут**: `google/gemini-3.1-pro-preview`
- Длительность **30–60 минут**: `google/gemini-3.5-flash`
- Длительность **> 60 минут**: `google/gemini-3-flash-preview`

**Фолбек-цепочка** (при ошибке/отказе — следующая модель):
1. `google/gemini-3.5-flash`
2. `google/gemini-3-flash-preview`

Если модель отвалилась — свериться со списком доступных: `curl -s https://openrouter.ai/api/v1/models | jq -r '.data[].id' | grep gemini`.

### 3. Транскрибация (запрос 1 к Gemini)

**Endpoint:** `POST https://openrouter.ai/api/v1/chat/completions`

**Headers:**
- `Authorization: Bearer $OPENROUTER_API_KEY`
- `Content-Type: application/json`
- `HTTP-Referer: https://hermes-agent.nousresearch.com`
- `X-Title: Hermes`

**Body:**
```json
{
  "model": "<выбранная модель>",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "text", "text": "Сделай подробную транскрибацию этого видео. Отформатируй в виде хорошо структурированного Markdown: выдели основные темы заголовками, используй списки для перечисления фактов и аргументов, разбей на смысловые блоки. Если в видеоряде есть важная визуальная информация (графики, карты, демонстрации, слайды, фотографии), опиши её в начале соответствующего блока *курсивом*. Указывай таймкоды в формате [MM:SS] для каждого блока. Ответь на русском языке."},
      {"type": "video_url", "video_url": {"url": "<YOUTUBE_URL>"}}
    ]
  }]
}
```

Ответ — `choices[0].message.content`.

⚠️ Запрос с `video_url` реально обрабатывается минуты (Gemini смотрит видеоряд). Таймаут ≥ 900–1800 с; это не «зависание». В `terminal` держать это в фоне (`background=true, notify=true`) или ставить `timeout` явно.

### 4. Саммаризация (запрос 2 к Gemini)

Тот же эндпоинт, но текст транскрибации **без** `video_url` (дешевле — без видео-токенов).

```json
{
  "model": "<та же модель>",
  "messages": [{
    "role": "user",
    "content": "Сделай краткое, но содержательное саммари следующей транскрибации видео. Отформатируй в виде структурированного Markdown: ключевые тезисы, главные выводы, важные детали. Сгруппируй по темам. Ответь на русском языке.\n\nТранскрибация:\n<TRANSCRIPT_TEXT>"
  }]
}
```

### 5. Сохранить в Notion

Создать страницу в датасорсе с `Тип1 = Конспект`.

**Название страницы** — через yt-dlp:
```bash
~/.hermes/tools/bin/yt-dlp --print title "URL" | tail -1
```

**Структура children:**
- Toggle «📝 Транскрибация» → полный текст транскрибации
- Toggle «📋 Саммари» → текст саммари
- Paragraph со ссылкой на оригинальное видео

⚠️ Транскрибация бывает длинной → разбивать на paragraph/heading_3 блоки по ~2000 символов.

Детали Notion API — в `references/notion-api.md`.

### 6. Ответ в чат

Hermes сам доставляет финальный ответ в Telegram-чат Паши — отдельный механизм отправки не нужен (в OpenClaw это делал канал сам, здесь это просто текст ответа).

**Видео < 10 минут:** три части в одном ответе (или несколькими сообщениями, если не влезает):
1. Полный текст транскрибации
2. Текст саммари
3. Ссылка на Notion-заметку

**Видео ≥ 10 минут:** один ответ — саммари + ссылка на Notion-заметку.

⚠️ Лимит сообщения Telegram — 4096 символов. Саммари часто длиннее → сжать до ~3500–3800 символов (главные выводы + тезисы по темам + цифры), ссылку на Notion оставить. Если совсем не влезает — сохранить полный текст в файл и отдать через `MEDIA:`.

## API-ключи

### OpenRouter

Ключ уже есть в окружении Hermes: `$OPENROUTER_API_KEY` (он же в `~/.hermes/.env`, строка `OPENROUTER_API_KEY=...`).

```bash
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-$(grep -m1 '^OPENROUTER_API_KEY=' ~/.hermes/.env | cut -d= -f2-)}"
```

⚠️ **Не выводить ключ в чат/логи** — передавать только в заголовок Authorization. Прежние источники из OpenClaw-версии (`~/.openclaw/agents/main/agent/auth-profiles.json`, SQLite `auth_profile_store`, `memorySearch.remote.apiKey`) в Hermes не существуют — не искать их.

### Notion

```bash
export NOTION_API_TOKEN="$(cat ~/.hermes/state/.notion_token)"
```

## Модели и фолбеки

| Длительность | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| ≤ 30 мин | `google/gemini-3.1-pro-preview` | `google/gemini-3.5-flash` | `google/gemini-3-flash-preview` |
| 30–60 мин | `google/gemini-3.5-flash` | `google/gemini-3-flash-preview` | — |
| > 60 мин | `google/gemini-3-flash-preview` | — | — |

## Edge cases

- Видео без субтитров — Gemini анализирует аудиодорожку (работает)
- 401 Unauthorized от OpenRouter → ключ берётся не оттуда; источник — `$OPENROUTER_API_KEY` / `~/.hermes/.env`
- Ошибка API — перейти к следующей модели из фолбек-цепочки
- yt-dlp недоступен — использовать oEmbed; если и он не дал длительность — считать видео коротким
- Токен Notion не умеет ни читать, ни удалять страницы
