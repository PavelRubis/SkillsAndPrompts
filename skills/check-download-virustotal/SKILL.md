---
name: check-download-virustotal
description: "Проверка скачанного файла/URL в VirusTotal перед запуском."
version: 1.0.1
license: MIT
author: Hermes Agent
platforms: [linux]
metadata:
  hermes:
    tags: [security, virustotal, downloads, supply-chain]
---

# Проверка загрузок в VirusTotal

## When to Use

Любой артефакт из интернета перед установкой/запуском: `curl … | sh`-скрипты, релизные бинарники (GitHub releases), npm/PyPI-пакеты, архивы с чужих сайтов. Если Паша даёт ссылку «поставь вот это» — проверка идёт **до** запуска и без напоминаний.

Железное правило Паши: **ничего не запускать и не устанавливать из интернета, не проверив артефакт в VirusTotal.** Правило действует и для `install.sh`, и для бинарников, и для npm/PyPI-пакетов.

## Порядок

1. Скачать артефакт в `~/.hermes/cache/scratch/` **без запуска**.
2. Посчитать `sha256sum`.
3. Проверить (скрипт скилла, ключ берётся сам из `~/.hermes/state/.virustotal_key`):

```bash
python3 ~/.hermes/skills/devops/check-download-virustotal/scripts/vt_check.py file /path/to/artifact
python3 ~/.hermes/skills/devops/check-download-virustotal/scripts/vt_check.py url https://example.com/install.sh
python3 ~/.hermes/skills/devops/check-download-virustotal/scripts/vt_check.py file /path --upload   # если VT файла не знает
```

4. Запускать только при `malicious + suspicious == 0`. Иначе — стоп и отчёт Паше, что именно сработало.
5. Для скриптов дополнительно: показать содержимое (или его ключевые строки) перед первым запуском, даже если VT чистый.

## API (что внутри)

- База: `https://www.virustotal.com/api/v3`, заголовок `x-apikey: <key>`
- Файл по хэшу: `GET /files/<sha256>` → `data.attributes.last_analysis_stats`
- URL: `GET /urls/<base64url(URL) без '='>`
- Неизвестный файл: `POST /files` с `-F file=@path` → `data.id` (analysis id) → опрашивать `GET /analyses/<id>`, пока `status != completed` (~30–60 с)
- Free tier: **4 запроса в минуту** → между запросами спать 15–16 с, иначе `QuotaExceededError`

## Трактовка вердикта

- Детекты считаются только `malicious` и `suspicious`. `timeout`, `type-unsupported`, `failure`, `undetected` — **не** детекты.
- Файл, которого VT не знает (`NotFoundError`), — это не «чисто». Либо загружать (`--upload`), либо проверять иначе (см. ниже).

## Дополнительные проверки без вердикта VT

- **npm:** смотреть `scripts` пакета на `preinstall`/`install`/`postinstall` — если есть, читать их глазами до установки. Ставить с `--ignore-scripts`.
- **PyPI:** сверять `sha256` с `urls[].digests.sha256` из `https://pypi.org/pypi/<pkg>/json`.
- **npm:** сверять с `dist.integrity` (sha512) из registry.
- Любая установка из `curl | sh` — сначала скачать файл, проверить, потом `bash file`.

## Грабли

- **Веб-интерфейс virustotal.com через `browser_exec` не открывается**: антибот отдаёт заглушку (`title: 🐴`, пустое тело). Работает только API.
- Ключ VT — 64 hex-символа, лежит в `~/.hermes/state/.virustotal_key` (chmod 600). Не печатать его в чат/логи; проверку формата делать без вывода значения.
- Загрузка файла в VT делает его доступным партнёрам VT. Для приватных артефактов (внутренние сборки, файлы с данными) сначала спросить Пашу.
- Хэш-поиск ничего не стоит по квоте, загрузка — тоже, но опрос анализа тратит запросы: не чаще раза в 12–15 с.
