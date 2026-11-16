---
name: "skill-git-dev"
description: "Разработка скиллов в git-репе: правка, дифф, аппрув, коммит, установка."
version: 0.2.0
author: Hermes Agent
platforms: [linux]
---

# Skill Git Dev

Полный цикл разработки скиллов, отслеживаемых в Git.
Триггер: Паша говорит «сделай/поправь скилл `<имя>`: `<что изменить>`» (в OpenClaw это была команда `/skill_git_dev`).

## Что нужно

- Git-репа склонирована в `~/work/SkillsAndPrompts`
- Рабочая ветка — **`hermes`** (в `master` лежат версии под OpenClaw, их не трогаем)
- Пуш идёт по SSH deploy key этого репозитория (write access включён), remote `origin` — `git@github.com:PavelRubis/SkillsAndPrompts.git`
- Приватный ключ лежит вне репозитория: `~/.hermes/state/id_github_deploy`, подставляется через `GIT_SSH_COMMAND` (см. шаг 8). Токены и ключи в репозитории не хранятся и в ответах не печатаются.

- Автор коммитов в репе:

```bash
git -C ~/work/SkillsAndPrompts config user.name "Hermes Agent"
git -C ~/work/SkillsAndPrompts config user.email "hermes@nousresearch.local"
```

## Порядок действий

### Шаг 1: Подготовить директорию разработки

```bash
mkdir -p ~/.hermes/cache/scratch/skill-dev/<имя>
```

Если скилл существует — скопировать его файлы из `~/work/SkillsAndPrompts/skills/<имя>/` в `~/.hermes/cache/scratch/skill-dev/<имя>/` (`SKILL.md` всегда, плюс `references/`, `scripts/`, `assets/` если есть). Старые файлы в директории разработки удалить — они могли остаться с прошлой сессии.

`~/.hermes/cache/scratch` чистится сам через 24 часа, поэтому это безопасная песочница.

### Шаг 2: Внести изменения

Правки в `~/.hermes/cache/scratch/skill-dev/<имя>/SKILL.md` и support-файлах.

### Шаг 3: Синхронизировать в репу

```bash
cp -r ~/.hermes/cache/scratch/skill-dev/<имя>/. ~/work/SkillsAndPrompts/skills/<имя>/
```

При добавлении **нового** скилла:

1. Прочитать `~/work/SkillsAndPrompts/Readme.md`
2. Взять `description` из frontmatter нового скилла
3. Добавить строку в таблицу скиллов, сохраняя алфавитный порядок:

```markdown
| `имя-скилла` | Описание из frontmatter SKILL.md |
```

4. Добавить `├── skill-name/` в блок дерева директорий

Если скилл удаляется — убрать его строку из таблицы и из дерева.

### Шаг 4: Показать изменения Паше

Ответить: «Скилл `<имя>` готов к коммиту. Вот изменения:» и приложить `git diff` из `~/work/SkillsAndPrompts` по всем изменённым/созданным файлам.

### Шаг 5: Подтвердить аппрув Паши

Дождаться явного одобрения. Не одобрил — вернуться к шагу 2 и пройти цикл заново.

### Шаг 6: Stage и коммит

```bash
cd ~/work/SkillsAndPrompts
git add skills/<имя>/
# если Readme.md обновлялся:
git add Readme.md
git commit -m "<описание на английском>"
```

### Шаг 7: Установить скилл в Hermes

Скиллы Hermes живут в `~/.hermes/skills/<категория>/<имя>/` и управляются тулом `skill_manage` (в OpenClaw это был `skill_workshop` — в Hermes его нет).

- **Существующий скилл:** `skill_manage(action="patch", name="<имя>", content=<полный SKILL.md из репы>)`
- **Новый скилл:** `skill_manage(action="create", name="<имя>", content=<SKILL.md>, category="<категория>")`
- **Support-файлы:** `skill_manage(action="write_file", name="<имя>", file_path="scripts/foo.py", file_content=...)`

Проверить, что скилл виден: `skill_view(name="<имя>")`.

### Шаг 8: Пуш

```bash
cd ~/work/SkillsAndPrompts
GIT_SSH_COMMAND="ssh -i ~/.hermes/state/id_github_deploy -o IdentitiesOnly=yes" git push origin hermes
```

Авторизация — только SSH-ключом; пароли и токены не запрашиваются и не печатаются.

### Шаг 9: Ответ

«Коммит `<хеш>`: `<сообщение>`» + подтверждение, что скилл установлен в Hermes.

## Правила коммит-сообщений

- На английском
- Короткий imperative-формат, заголовок до 72 символов
- Описывать ЧТО изменилось: `add retry logic to yandex-reviews-analyzer`, `update notion-task-create frontmatter`

## Заметки

- Авторизация — только SSH deploy key, привязанный к этому репозиторию. Никакие токены в репо и в ответах не появляются.
- Ветка `hermes` — единственная, куда пушит агент. Merge в `master` — решение Паши.
