# Notion API для youtube-analyzer

## Переменные окружения

```bash
export NOTION_API_TOKEN="$(cat ~/.hermes/state/.notion_token)"
```

⚠️ **Права токена (проверено):** читает схемы и содержимое страниц, создаёт страницы. `PATCH` и `DELETE` уже существующих блоков → **403 Forbidden** (проверено и на смене типа блока, и на удалении). Следствие: вложенность и порядок блоков финальны с момента `POST /v1/pages` — «накидать плоско, потом обернуть в toggle» невозможно.

## Дозапись внутрь toggle

Toggle создаётся сразу с первыми ≤95 детьми, остальное доливается в сам toggle (а не в страницу):

```bash
curl -sS "https://api.notion.com/v1/blocks/$PAGE_ID/children?page_size=100" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" -H "Notion-Version: 2026-03-11"

curl -sS -X PATCH "https://api.notion.com/v1/blocks/$TOGGLE_ID/children" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" -H "Notion-Version: 2026-03-11" \
  -H "Content-Type: application/json" \
  -d '{"children": [...]}'
```

Дозапись детей в toggle работает — 403 только на изменение/удаление уже существующих блоков. Пачки ≤95 блоков; готовый цикл — `scripts/notion_md_blocks.py` в корне скилла.

## ID датасорса

Data Source ID: `63686c23-7a55-4126-95b3-93b9e49b9820`

**Parent всегда `data_source_id`**, а не `database_id` (с `database_id` будет 404).

## Создание страницы

```bash
curl -sS "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2026-03-11" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"data_source_id": "63686c23-7a55-4126-95b3-93b9e49b9820"},
    "properties": {
      "Название": {"title": [{"text": {"content": "НАЗВАНИЕ ВИДЕО"}}]},
      "Тип1": {"select": {"name": "Конспект"}}
    },
    "children": [...]
  }'
```

## Блоки

### Toggle с заголовком и детьми

```json
{
  "object": "block",
  "type": "toggle",
  "toggle": {
    "rich_text": [{"type": "text", "text": {"content": "📝 Транскрибация"}}],
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Текст..."}}]}}
    ]
  }
}
```

### Heading 3 (внутри toggle для структуры)

```json
{
  "object": "block",
  "type": "heading_3",
  "heading_3": {"rich_text": [{"type": "text", "text": {"content": "Заголовок раздела"}}]}
}
```

### Параграф со ссылкой на оригинал

```json
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {"type": "text", "text": {"content": "🔗 Оригинал: "}},
      {"type": "text", "text": {"content": "https://youtube.com/...", "link": {"url": "https://youtube.com/..."}}}
    ]
  }
}
```

## Разбивка длинного текста

- Каждый смысловой абзац → отдельный paragraph-блок
- Заголовки (из Markdown от Gemini) → heading_3 блоки
- Строки длиннее ~2000 символов — разбивать на несколько paragraph-блоков
- Лимит Notion API: 1000 блоков на запрос

## URL созданной страницы

```bash
URL_ID="${PAGE_ID//-/}"
echo "https://notion.so/$URL_ID"
```
