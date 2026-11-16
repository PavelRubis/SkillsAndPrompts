---
name: "notion-task-create"
description: "Задачи в Notion-базе через raw API: токен, database ID, свойства."
version: 0.2.0
author: Hermes Agent
platforms: [linux]
---

# Notion Task Create

Создание задач в базе задач Notion через raw API (curl).
Markdown-эндпоинт (`ntn pages create`, Notion MCP) **не пробрасывает свойства базы** — только контент страницы.
Поэтому используем прямой POST на `/v1/pages` с явным JSON.

## Переменные окружения

```bash
export NOTION_API_TOKEN="$(cat ~/.hermes/state/.notion_token)"
```

⚠️ Токен умеет **только создавать** страницы. Не читать, не обновлять, не удалять.

Если файла `~/.hermes/state/.notion_token` нет — сказать Паше, что нужен файл с токеном (в чат токен не просить).

## ID базы задач

```
684555f9-6205-4461-ada8-db162c937ecd
```

## Известные свойства базы

| Свойство | Тип | Пример |
|---|---|---|
| `Название` | title | `{"title":[{"text":{"content":"Текст задачи"}}]}` |
| `Дата выполнения` | date | `{"date":{"start":"2026-06-27"}}` |

⚠️ Если нужны другие свойства — спросить пользователя (токен не позволяет читать схему).

## Создание задачи (curl)

```bash
export NOTION_API_TOKEN="$(cat ~/.hermes/state/.notion_token)"

curl -sS "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2026-03-11" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "684555f9-6205-4461-ada8-db162c937ecd"},
    "properties": {
      "Название": {"title": [{"text": {"content": "НАЗВАНИЕ ЗАДАЧИ"}}]},
      "Дата выполнения": {"date": {"start": "YYYY-MM-DD"}}
    }
  }'
```

## Контент страницы (children)

Чтобы добавить описание внутрь страницы, добавить `children` в тело запроса:

```json
"children": [
  {
    "object": "block",
    "type": "paragraph",
    "paragraph": {
      "rich_text": [{"type": "text", "text": {"content": "Текст описания."}}]
    }
  }
]
```

## Отправка ссылки пользователю

URL собирается из ID страницы (убрать все дефисы):
```
https://notion.so/<page-id-without-dashes>
```

Пример: `385a426d-c624-8128-ab6c-e703b4e19125` → `https://notion.so/385a426dc6248128ab6ce703b4e19125`

## Частые грабли

- **Токен:** всегда читать из `~/.hermes/state/.notion_token`, не хардкодить
- **Markdown-эндпоинт не работает для свойств** — только raw API с явным JSON
- **Parent:** `database_id`, не `data_source_id` (эта база не датасорс)
- **Дефисы в URL:** убрать все дефисы из ID страницы
- **Треш-страниц:** старые тестовые страницы не удалить (токен без прав на удаление), просто оставлять
