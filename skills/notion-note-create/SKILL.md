---
name: "notion-note-create"
description: "Создание заметок в Notion-датасорсе: токен, Тип1, контент, to-do для списка покупок."
---

# Notion Note Create

Создание обычных заметок в Notion через raw API (curl).  
`ntn pages create` (Markdown) **не пробрасывает свойства базы** — используем прямой POST `/v1/pages`.

## Переменные окружения

```bash
export NOTION_API_TOKEN="$(cat ~/.openclaw/workspace/state/.notion_token)"
export NOTION_API_VERSION=2026-03-11
```

⚠️ Токен умеет **только создавать** страницы. Не читать, не обновлять, не удалять.

## ID базы (data source)

База заметок и дневника — одна и та же, это **датасорс** (не обычная база данных).  
Parent: `data_source_id`, а НЕ `database_id`.

Data Source ID: `63686c23-7a55-4126-95b3-93b9e49b9820`

## Обязательные правила

1. Всегда устанавливать свойство `Тип1` (select)
2. После создания — отправить ссылку: `https://notion.so/<page-id-без-дефисов>`
3. Для голосовых/текстовых заметок: сначала полная транскрибация/исходный текст, затем `---`, затем саммари
4. **Parent всегда `data_source_id`**, а не `database_id`

## Возможные значения Тип1 (select)

| Значение |
|---|
| Сериал |
| Фильм |
| Аниме |
| Документ |
| Флитинг |
| Список покупок |
| Рецепт |
| Ссылка |
| Идея |
| Прогресс по качалке |
| Конспект |
| Плюсы и минусы |
| Место |
| Инсайт |
| Сон |
| Топ секрет |
| Дневник |
| Брейншторм |

⚠️ `Дневник` — не использовать в этом скилле (для него отдельный механизм через `diary_buffer.json`).

Если Паша называет Тип1 не из списка — уточнить, какой из существующих использовать.

## Создание заметки (curl)

```bash
export NOTION_API_TOKEN="$(cat ~/.openclaw/workspace/state/.notion_token)"
export NOTION_API_VERSION=2026-03-11
DS_ID="63686c23-7a55-4126-95b3-93b9e49b9820"

curl -sS "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2026-03-11" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"data_source_id": "'"$DS_ID"'"},
    "properties": {
      "Название": {"title": [{"text": {"content": "ЗАГОЛОВОК"}}]},
      "Тип1": {"select": {"name": "ЗНАЧЕНИЕ_ТИП1"}}
    },
    "children": [...]
  }'
```

## Формат контента

### Обычная заметка

Стандартные блоки: `paragraph`, `heading_1/2/3`, `bulleted_list_item`, `numbered_list_item`.

### Голосовая/текстовая заметка (транскрибация + саммари)

```
Транскрибация:
<полный текст того, что сказал Паша>

---

Саммари:
<краткое изложение>
```

Каждый абзац — отдельный `paragraph` блок.

### Список покупок (особая обработка)

Когда `Тип1 = Список покупок`, контент оформляется как **to-do список**:

```json
"children": [
  {
    "object": "block",
    "type": "to_do",
    "to_do": {
      "rich_text": [{"type": "text", "text": {"content": "Молоко"}}],
      "checked": false
    }
  },
  {
    "object": "block",
    "type": "to_do",
    "to_do": {
      "rich_text": [{"type": "text", "text": {"content": "Хлеб"}}],
      "checked": false
    }
  }
]
```

Каждая позиция покупки — отдельный `to_do` блок с `checked: false`.

## Ссылка на статью с Хабра (Тип1 = Ссылка)

Триггер: Паша присылает ссылку на статью с Хабра — в том числе в замаскированном виде (habr.com/ru/articles/..., habr.com/ru/news/..., `share.google/...` и другие короткие ссылки).

Алгоритм:

1. Прочитать все ресурсы из базы «Resources»(см. ниже) — получить `Name` и id каждой страницы-ресурса.
2. Перейти по ссылке (`web_fetch`) и прочитать немного текста статьи. **Если ссылка короткая/замаскированная** — сначала развернуть редирект (см. ниже).
3. По тексту статьи определить, к каким ресурсам её можно прилинковать. Ресурсов может быть 0, 1, 2 и больше. Если подходящего ресурса нет — не линковать вообще.
4. Создать заметку:
   - `Название` = `<Заголовок статьи>` + `" Хабр"`
   - `Тип1` = `Ссылка`
   - `💎 Ресурсы` = список id ресурсов для линковки (relation)
5. Контент страницы (`children`) — **только ссылка на статью**, больше ничего.

### Короткие / замаскированные ссылки

Ссылка на статью может приходить в «замаскированном» виде, например через Google Share:

```
https://share.google/C0aZ6H6tbd0XHNQhO
```

Перед чтением статьи такие ссылки нужно **развернуть** до реального URL. Надёжный способ — `web_fetch`: он сам следует редиректу, а финальный URL виден в поле `finalUrl` ответа:

```
web_fetch { "url": "https://share.google/C0aZ6H6tbd0XHNQhO" }
→ { "url": "https://share.google/...", "finalUrl": "https://habr.com/ru/articles/1082572/", ... }
```

Именно `finalUrl` (например `https://habr.com/ru/articles/XXXXXX/`) использовать как ссылку в контенте заметки.

⚠️ `curl -I -L` для `share.google` **не работает** — отдаёт промежуточный `google.com/share.google?q=...`, а не статью. Редирект там клиентский. Поэтому только `web_fetch`.

Если развернуть не удалось (не Хабр / не статья) — спросить Пашу, что это за ссылка.

### База «Resources» (датасорс ресурсов)

Data Source ID: `058c79a8-e8f0-431b-b467-b9de20f4e61d`

Свойство с названием ресурса — `Name` (title).

Чтение всех ресурсов:

```bash
export NOTION_API_TOKEN="$(cat ~/.openclaw/workspace/state/.notion_token)"
export NOTION_API_VERSION=2026-03-11
RES_DS_ID="058c79a8-e8f0-431b-b467-b9de20f4e61d"

curl -sS -x http://127.0.0.1:9080 \
  "https://api.notion.com/v1/data_sources/$RES_DS_ID/query" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2026-03-11" \
  -H "Content-Type: application/json" \
  -d '{"page_size": 100}'
```

Постранично (`start_cursor` / `has_more`), пока не соберутся все ресурсы.

### Свойство `💎 Ресурсы`

На датасорсе заметок есть relation-свойство `💎 Ресурсы`, ведущее на датасорс `058c79a8-...` (Resources).

Установка при создании страницы:

```json
"💎 Ресурсы": {"relation": [{"id": "<page-id-ресурса>"}, {"id": "<page-id-ресурса-2>"}]}
```

Если ни один ресурс не подошёл — свойство не передавать (оставить пустым).

### Пример создания заметки-ссылки

```bash
export NOTION_API_TOKEN="$(cat ~/.openclaw/workspace/state/.notion_token)"
export NOTION_API_VERSION=2026-03-11
DS_ID="63686c23-7a55-4126-95b3-93b9e49b9820"

curl -sS -x http://127.0.0.1:9080 "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2026-03-11" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"data_source_id": "'"$DS_ID"'"},
    "properties": {
      "Название": {"title": [{"text": {"content": "ЗАГОЛОВОК СТАТЬИ Хабр"}}]},
      "Тип1": {"select": {"name": "Ссылка"}},
      "💎 Ресурсы": {"relation": [{"id": "RESOURCE_PAGE_ID"}]}
    },
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "https://habr.com/ru/articles/XXXXXX/", "link": {"url": "https://habr.com/ru/articles/XXXXXX/"}}}]}}
    ]
  }'
```

## Ссылка на созданную страницу

```bash
# Из ответа API берём id, убираем все дефисы
PAGE_ID="385a426d-c624-8128-ab6c-e703b4e19125"
URL_ID="${PAGE_ID//-/}"
echo "https://notion.so/$URL_ID"
```

## Частые грабли

- **Токен:** всегда читать из `state/.notion_token`, не хардкодить
- **Markdown-эндпоинт не работает для свойств** — только raw API с явным JSON
- **Parent:** `data_source_id`, НЕ `database_id` (это датасорс, с `database_id` будет 404)
- **Дефисы в URL:** убрать все дефисы из ID страницы
- **Тип1 обязателен:** без него не создавать заметку — спросить Пашу
- **Треш-страниц:** старые тестовые страницы не удалить (токен без прав на удаление)
- **Список покупок:** использовать `to_do` блоки, не обычный текст
