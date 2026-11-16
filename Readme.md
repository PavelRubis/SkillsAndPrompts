# Skills and Prompts

Личный репозиторий с системными промптами и прикладными навыками для AI-ассистентов.

Здесь собраны инструкции, которые задают поведение модели: язык общения, подход к анализу вопросов, правила работы с источниками, формат ответов и конкретные workflow для повторяющихся задач.

## Ветки

| Ветка | Для кого |
|---|---|
| `hermes` | Hermes Agent (эта машина): `~/.hermes/...`, cron через `cronjob_manage`, скиллы через `skill_manage`, веб через `web_search`/`web_extract`, браузер через `browser_exec`. |
| `master` | Исходная версия под OpenClaw (`~/.openclaw/workspace/state`, `cron get/update`, `skill_workshop`, `web_fetch`, плагины в `plugins.entries`). |

Ветки расходятся только в интеграционных местах — логика навыков общая.

## Что внутри

```text
.
├── system-prompts/
│   ├── ChatGPT.md
│   └── OpenWebUI.md
└── skills/
    ├── diary/
    │   ├── SKILL.md
    │   └── scripts/
    │       └── diary_reminder.py
    ├── idea-reality-check/
    │   └── SKILL.md
    ├── notion-note-create/
    │   └── SKILL.md
    ├── notion-task-create/
    │   └── SKILL.md
    ├── skill-git-dev/
    │   └── SKILL.md
    ├── skill-git-sync/
    │   └── SKILL.md
    ├── yandex-reviews-analyzer/
    │   └── SKILL.md
    └── youtube-analyzer/
        ├── SKILL.md
        └── references/
            └── notion-api.md
```

## System Prompts

`system-prompts/` содержит базовые инструкции для настройки поведения ассистента в разных интерфейсах.

| Файл | Назначение |
|---|---|
| `system-prompts/ChatGPT.md` | Инструкции для ChatGPT: русский язык, обращение к Паше, экспертный стиль ответа, требования к источникам и формату. |
| `system-prompts/OpenWebUI.md` | Вариант системного промпта для OpenWebUI с дополнительными правилами по веб-поиску через MCP. |

## Skills

`skills/` содержит отдельные навыки в формате `SKILL.md`. Каждый навык описывает, когда он должен включаться, какие инструменты использовать и какой результат вернуть.

| Навык | Для чего нужен |
|---|---|
| `diary` | Дневник через Notion Data Source: буфер записей в JSON-файле, напоминание 20:00 MSK (скрипт без LLM), автосоздание заметки 22:00 MSK. |
| `idea-reality-check` | Проверка конкурентности идеи через `idea-reality-mcp`: GitHub, Hacker News, npm, PyPI, Product Hunt и Stack Overflow. |
| `notion-note-create` | Создание заметок в Notion-датасорсе через raw Notion API. Поддерживает типы заметок и особый формат для списков покупок. |
| `notion-task-create` | Создание задач в базе Notion через raw API с явным заполнением свойств. |
| `skill-git-dev` | Git-воркфлоу разработки скиллов: правка, дифф, аппрув, коммит, установка через `skill_manage`, пуш. |
| `skill-git-sync` | Sync skills from Git repo: pull ветки `hermes`, install/update a skill by name. Trigger: актуализируй |
| `yandex-reviews-analyzer` | Сбор и анализ негативных отзывов с Яндекс.Карт, сортировка по критичности и подготовка отчета. |
| `youtube-analyzer` | Анализ YouTube-видео через Gemini/OpenRouter: транскрибация, саммари, сохранение результата в Notion и ответ в чат. |

## Как использовать

### Системные промпты

1. Открой нужный файл из `system-prompts/`.
2. Скопируй содержимое в системные инструкции выбранного интерфейса.
3. При необходимости адаптируй отдельные правила под конкретную среду.

### Навыки (Hermes)

1. Найди нужный каталог в `skills/`.
2. Открой `SKILL.md` и support-файлы (`scripts/`, `references/`).
3. Установи навык тулом `skill_manage` (`create` для нового, `patch` с полным `content` для существующего, `write_file` для support-файлов). Целевой каталог — `~/.hermes/skills/<категория>/<имя>/`.
4. Проверь зависимости, указанные внутри навыка: API-токены, MCP-серверы, CLI-инструменты, локально установленные сборщики.

## Зависимости и секреты

Некоторые навыки рассчитаны на внешние сервисы и локальную инфраструктуру:

- Notion API token — файл `~/.hermes/state/.notion_token` (chmod 600)
- OpenRouter API key — `~/.hermes/.env`, переменная `OPENROUTER_API_KEY`
- Gemini-модели через OpenRouter
- `yt-dlp` — `~/.hermes/tools/bin/yt-dlp`
- `@sharleysoft/openclaw-yandex-maps-places-review` — локальная установка в `~/.hermes/tools/yandex-reviews/` + Playwright headless shell
- `idea-reality-mcp` — MCP-сервер, подключается к Hermes (`manage_connections`, `mcp: true`)
- Пуш в репозиторий — SSH deploy key с write access (приватный ключ хранится вне репозитория)

Секреты не должны храниться в репозитории. В самих навыках описано, откуда читать токены в рабочей среде и какие переменные окружения нужны.

## Принципы

- Инструкции пишутся так, чтобы ассистент мог выполнить задачу целиком, а не просто дать общую рекомендацию.
- Workflow фиксируют реальные грабли: ограничения API, особенности DOM, fallback-модели, формат итогового ответа.
- Каждый навык должен иметь понятный триггер, ожидаемый результат и список зависимостей.
- README описывает только карту репозитория; детали выполнения остаются внутри соответствующих `SKILL.md`.

## Кодировка

Все Markdown-файлы предполагаются в UTF-8.
