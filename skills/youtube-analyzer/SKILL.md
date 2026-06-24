---
name: "youtube-analyzer"
description: "Анализ YouTube через Gemini: транскрибация + саммари, сохранение в Notion. Триггер — ссылка ютуб"
---

# YouTube Analyzer

Анализирует YouTube-видео через Google Gemini (OpenRouter API) и сохраняет результат в Notion.

## Триггер

Кинуть ссылку на YouTube с опциональными ключевыми словами:

- `https://youtube.com/watch?v=...` — полный анализ (транскрибация + саммари)
- `https://youtube.com/watch?v=... транскрибация` — только транскрибация
- `https://youtube.com/watch?v=... саммари` — только саммари

Слова могут быть в любом месте сообщения (до или после ссылки).

## Workflow

### 1. Получить длительность видео

**Primary:** yt-dlp
```bash
/tmp/yt-dlp --print duration_string "URL"
```
Если бинарника нет — скачать:
```bash
curl -sL "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux" -o /tmp/yt-dlp && chmod +x /tmp/yt-dlp
```

**Fallback:** YouTube oEmbed
```
https://www.youtube.com/oembed?url=URL&format=json
```
Спарсить `duration_seconds` (если есть в ответе).

### 2. Выбрать модель

- Длительность **≤ 30 минут**: `google/gemini-3.1-pro-preview`
- Длительность **30–60 минут**: `google/gemini-3.5-flash`
- Длительность **> 60 минут**: `google/gemini-3-flash-preview`

**Фолбек-цепочка** (при ошибке/отказе — перейти к следующей):
1. `google/gemini-3.5-flash`
2. `google/gemini-3-flash-preview`

### 3. Транскрибация (запрос 1 к Gemini)

Отправить запрос через OpenRouter API с `video_url` (ютуб-ссылка).

**Endpoint:** `POST https://openrouter.ai/api/v1/chat/completions`

**Headers:**
- `Authorization: Bearer <OPENROUTER_API_KEY>`
- `Content-Type: application/json`
- `HTTP-Referer: https://openclaw.ai`
- `X-Title: OpenClaw`

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

Извлечь ответ из `choices[0].message.content`.

### 4. Саммаризация (запрос 2 к Gemini)

Отправить текст транскрибации **без** video_url (дешевле — без видео-токенов).

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

Создать страницу в датасорсе с Тип1="Конспект".

**Название страницы:** получить через yt-dlp:
```bash
/tmp/yt-dlp --print title "URL"
```

**Структура children:**
- Toggle "📝 Транскрибация" → внутри полный текст транскрибации
- Toggle "📋 Саммари" → внутри текст саммари
- Paragraph со ссылкой на оригинальное видео

⚠️ Транскрибация может быть длинной → разбивать на paragraph/heading_3 блоки по ~2000 символов.

Детали Notion API — в `references/notion-api.md`.

### 6. Отправить в Telegram

**Видео < 10 минут:** три сообщения:
1. Полный текст транскрибации
2. Текст саммари
3. Ссылка на Notion-заметку

**Видео ≥ 10 минут:** одно сообщение:
1. Саммари + ссылка на Notion-заметку

## API-ключи

OpenRouter — из конфига OpenClaw:
```python
import json
with open('/home/openclawrunner/.openclaw/openclaw.json') as f:
    config = json.load(f)
api_key = config['agents']['defaults']['memorySearch']['remote']['apiKey']
```

Notion — из файла:
```bash
export NOTION_API_TOKEN="$(cat ~/.openclaw/workspace/state/.notion_token)"
export NOTION_API_VERSION=2026-03-11
```

## Модели и фолбеки

| Длительность | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| ≤ 30 мин | `google/gemini-3.1-pro-preview` | `google/gemini-3.5-flash` | `google/gemini-3-flash-preview` |
| 30–60 мин | `google/gemini-3.5-flash` | `google/gemini-3-flash-preview` | — |
| > 60 мин | `google/gemini-3-flash-preview` | — | — |

## Edge cases

- Видео без субтитров — Gemini анализирует аудиодорожку (работает)
- Ошибка API — перейти к следующей модели из фолбек-цепочки
- yt-dlp недоступен — использовать oEmbed; если оба недоступны — считать видео коротким
- Токен Notion не умеет ни читать, ни удалять страницы
