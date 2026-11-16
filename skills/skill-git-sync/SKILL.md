---
name: "skill-git-sync"
description: "Sync skills from git: pull hermes, install/update skill. Trigger: актуализируй"
version: 0.2.0
author: Hermes Agent
platforms: [linux]
---

# Skill Git Sync

Триггер: Паша говорит «актуализируй `<имя-скилла>`».

## Что нужно

- Git-репа склонирована в `~/work/SkillsAndPrompts`
- Рабочая ветка — `hermes` (версии под Hermes; в `master` — под OpenClaw)
- Пулл и пуш идут по SSH deploy key репозитория (remote `git@github.com:PavelRubis/SkillsAndPrompts.git`); детали — в навыке `skill-git-dev`

## Порядок действий

### 1. Pull последней версии ветки hermes

```bash
cd ~/work/SkillsAndPrompts && git pull origin hermes
```

### 2. Проверить, есть ли скилл в репе

Проверить наличие `skills/<имя>/SKILL.md`.

Если НЕ найден:
- Найти похожие по названию каталоги в `skills/`
- Ответить: «Скилл `<имя>` не найден в репозитории. Похожие: `<список>`. Какой ты имел в виду?»
- Ждать ответа Паши

### 3. Прочитать скилл из репы

Прочитать `skills/<имя>/SKILL.md` полностью, плюс support-файлы (`references/`, `scripts/`, `assets/`).

### 4. Установить или обновить в Hermes

Скиллы Hermes лежат в `~/.hermes/skills/<категория>/<имя>/`; установка — только через `skill_manage` (тула `skill_workshop`, как в OpenClaw, в Hermes нет).

**Если скилл уже установлен (`skill_view(name=<имя>)` отвечает):**
- `skill_manage(action="patch", name="<имя>", content=<полный SKILL.md из репы>)`
- Support-файлы: `skill_manage(action="write_file", name="<имя>", file_path="references/x.md", file_content=...)`

**Если скилл новый:**
- `skill_manage(action="create", name="<имя>", content=<SKILL.md>, category="<категория>")`
- затем `write_file` для каждого support-файла

⚠️ Перед созданием помнить про лимит: `description` в frontmatter Hermes показывает индекс навыков и должен быть коротким (в идеале ≤ 60 символов). В репе описания длиннее — при установке можно оставить как есть, но при обновлении индекса лучше сокращать.

### 5. Ответить

«Скилл `<имя>` актуализирован из ветки hermes.»
