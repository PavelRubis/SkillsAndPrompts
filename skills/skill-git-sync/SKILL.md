---
name: "skill-git-sync"
description: "Sync skills from Git repo: pull master, install/update a skill by name. Trigger: актуализируй"
---

# Skill Git Sync

Триггер: Паша говорит «актуализируй <имя-скилла>».

## Что нужно

- Git-репа склонирована в `state/skills-repo/`
- GitHub fine-grained токен лежит в `state/.github_token`
- Remote `origin` использует `https://oauth2:<token>@github.com/...` для push-доступа

## Порядок действий

### 1. Pull последней версии master

cd state/skills-repo && git pull origin master

### 2. Проверить, есть ли скилл в репе

Проверить наличие `skills/<имя>/SKILL.md` в репе.

Если НЕ найден:
- Найти в `state/skills-repo/skills/` похожие по названию скиллы.
- Ответить: «Скилл `<имя>` не найден в репозитории. Вот похожие: `<список>`. Какой ты имел в виду?»
- Ждать ответа Паши.

### 3. Прочитать скилл из репы

Прочитать `state/skills-repo/skills/<имя>/SKILL.md` полностью.

Также проверить support-файлы в `state/skills-repo/skills/<имя>/` (references/, scripts/, assets/).

### 4. Установить или обновить

**Если скилл уже есть в `workspace/skills/<имя>/`:**
- Вызвать `skill_workshop` с `action=update`, `skill_name=<имя>`, передав SKILL.md из репы как `proposal_content`.
- Скопировать support-файлы из репы в `workspace/skills/<имя>/`.
- Вызвать `skill_workshop` с `action=apply` и proposal_id из обновления.

**Если скилл новый (нет в workspace):**
- Вызвать `skill_workshop` с `action=create`, `name=<имя>`, передав SKILL.md из репы как `proposal_content`.
- Скопировать support-файлы из репы в `workspace/skills/<имя>/`.
- Вызвать `skill_workshop` с `action=apply`.

### 5. Ответить

«Скилл `<имя>` актуализирован из master.»
