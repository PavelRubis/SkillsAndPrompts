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

⚠️ **Права токена (проверено 2026-11-16):** читает схемы датасорсов и содержимое страниц, создаёт страницы. Обновление и удаление **не проверялись** — на них не рассчитывать.

Если файла `~/.hermes/state/.notion_token` нет — сказать Паше, что нужен файл с токеном (в чат токен не просить).

## ID базы задач

База задач — это **контейнер** (`684555f9-6205-4461-ada8-db162c937ecd`) с одним **датасорсом**:

```
Data Source ID: 4e4bc143-14e8-4ecc-90a5-a121efa18501
```

⚠️ `GET /v1/databases/684555f9-...` отдаёт 0 свойств — схема живёт на датасорсе. Поэтому страницу задачи создавать с `parent: {data_source_id: "4e4bc143-..."}`, а НЕ с `database_id`.

Схему можно перечитывать в любой момент:

```bash
curl -sS "https://api.notion.com/v1/data_sources/4e4bc143-14e8-4ecc-90a5-a121efa18501" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2026-03-11"
```

## Известные свойства датасорса

| Свойство | Тип | Пример |
|---|---|---|
| `Название` | title | `{"title":[{"text":{"content":"Текст задачи"}}]}` |
| `Дата выполнения` | date | `{"date":{"start":"2026-06-27"}}` |
| `Дата начала` | date | `{"date":{"start":"2026-06-27"}}` |
| `Отсрочена до` | date | `{"date":{"start":"2026-07-01"}}` |
| `Приоритет` | select | `{"select":{"name":"ASAP"}}` — опции: `ASAP, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1` |
| `GTD-статус` | select | `{"select":{"name":"Do next"}}` — опции: `Do next, Когда-нибудь` |

Остальные свойства — formula/rollup/relation/button (`Состояние`, `Завершена`, `Просрочена`, `📌 Заметки`, `Подзадачи`, `Связанные задачи` и т.п.): их не заполнять, Notion считает их сам. Полный список — из запроса схемы выше.

Если нужно свойство, которого нет в таблице — прочитать схему, а не угадывать.

## Создание задачи (curl)

```bash
export NOTION_API_TOKEN="$(cat ~/.hermes/state/.notion_token)"

curl -sS "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2026-03-11" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"data_source_id": "4e4bc143-14e8-4ecc-90a5-a121efa18501"},
    "properties": {
      "Название": {"title": [{"text": {"content": "НАЗВАНИЕ ЗАДАЧИ"}}]},
      "Дата выполнения": {"date": {"start": "YYYY-MM-DD"}},
      "Приоритет": {"select": {"name": "ASAP"}}
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
- **Parent:** `data_source_id` `4e4bc143-...`, НЕ `database_id` контейнера (`684555f9-...`): у контейнера нет свойств, страница получится пустой или вернёт ошибку
- **Схема читается:** `GET /v1/data_sources/4e4bc143-...` — брать список свойств и опции select оттуда, а не из памяти
- **Дата со временем:** нужен конкретный час — `{"date":{"start":"YYYY-MM-DDTHH:MM:00+03:00"}}`; date-only (`YYYY-MM-DD`) даёт задачу без времени
- **Повторное создание:** перед POST запросить датасорс по `Дата выполнения` за нужный день и сравнить `Название` — иначе cron-скрипт наплодит дублей на повторном/ручном запуске
- **Cron-скрипты только на stdlib:** `urllib.request` вместо `requests` — у python планировщика requests нет (подробнее — скилл hermes-agent, файл references/background-systems.md)
- **Дефисы в URL:** убрать все дефисы из ID страницы
- **Треш-страниц:** старые тестовые страницы не удалить (токен без прав на удаление), просто оставлять
