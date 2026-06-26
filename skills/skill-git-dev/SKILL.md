---
name: "skill-git-dev"
description: "Git-based skill dev workflow: after approval and apply, commit changes to master."
---

# Skill Git Dev

Covers the full development cycle for skills tracked in Git. Trigger: after user approves and applies a skill change during collaborative development.

## Prerequisites

- Git repo cloned at `state/skills-repo/`
- GitHub fine-grained token saved in `state/.github_token`
- Git config in repo set:
  - `user.name`: Clow
  - `user.email`: clow@openclaw.local

## Workflow

### When to commit

Commit after ALL of:
1. User explicitly approves the skill change
2. The skill is applied via `skill_workshop apply`
3. User confirms the change is working (if testing was needed)

Never commit before user approval.

### Step 1: Sync skill files to repo

Copy updated files from `workspace/skills/<name>/` to `state/skills-repo/skills/<name>/`:

- `SKILL.md` always
- `references/`, `scripts/`, `assets/` if they exist

### Step 2: Stage and commit

```bash
cd state/skills-repo
git add skills/<name>/
git commit -m "<imperative English description>"
```

### Step 3: Push

```bash
git push origin master
```

### Step 4: Report

Reply with commit hash and summary: "Committed `<hash>`: `<message>`"

## Commit message rules

- Write in English
- Use short imperative form (max 72 chars for summary line)
- Describe WHAT changed: "add retry logic to yandex-reviews-analyzer", "update notion-task-create frontmatter"
- If multiple skills changed in one session, commit each skill separately

## Notes

- Token is stored in `state/.github_token` (chmod 600), never expose it in logs or replies
- Remote URL contains the token inline — keep repo directory private
