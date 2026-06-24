# Notion API для youtube-analyzer

## Переменные окружения

```bash
export NOTION_API_TOKEN="$(cat ~/.openclaw/workspace/state/.notion_token)"
export NOTION_API_VERSION=2026-03-11
```

⚠️ Токен умеет **только создавать** страницы. Не читать, не обновлять, не удалять.

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
