#!/usr/bin/env python3
"""Напоминалка дневника для Hermes cron (режим no_agent).

Печатает напоминание ТОЛЬКО если в буфере нет записей за сегодня (MSK).
Пустой stdout = cron ничего не отправит Паше.

Установка: скопировать в ~/.hermes/scripts/diary_reminder.py
Cron: cronjob_manage(action="create", schedule="0 20 * * *", no_agent=True,
                     script="diary_reminder.py", timezone="Europe/Moscow")
"""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BUFFER = Path(os.path.expanduser("~/.hermes/state/diary_buffer.json"))
MSK = ZoneInfo("Europe/Moscow")
REMINDER = "Сегодня ещё ничего не добавлено в дневник. Может, есть что записать?"


def should_remind() -> bool:
    try:
        data = json.loads(BUFFER.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return True

    if data.get("date") != datetime.now(MSK).strftime("%Y-%m-%d"):
        return True

    return not data.get("entries")


if __name__ == "__main__":
    if should_remind():
        print(REMINDER)
