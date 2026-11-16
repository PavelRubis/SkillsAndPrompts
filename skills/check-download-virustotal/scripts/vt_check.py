#!/usr/bin/env python3
"""Проверка файла или URL в VirusTotal.

Использование:
    vt_check.py file /path/to/artifact [--upload]
    vt_check.py url https://example.com/install.sh

Ключ: ~/.hermes/state/.virustotal_key (64 hex-символа).
Выход: строка вердикта + exit 0 (чисто) / 1 (детекты или неизвестный файл).
"""

import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

KEY_PATH = os.path.expanduser("~/.hermes/state/.virustotal_key")
API = "https://www.virustotal.com/api/v3"


def api_key() -> str:
    key = open(KEY_PATH, encoding="utf-8").read().strip()
    if len(key) != 64 or any(c not in "0123456789abcdefABCDEF" for c in key):
        sys.exit("Ключ VirusTotal не найден или неверного формата")
    return key


def get(path: str, key: str) -> dict:
    req = urllib.request.Request(f"{API}/{path}", headers={"x-apikey": key})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try:
            return json.loads(body)
        except Exception:
            return {"error": {"code": str(e.code), "message": body[:200]}}


def upload(path: str, key: str) -> dict:
    import mimetypes
    import uuid

    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        data = f.read()
    name = os.path.basename(path)
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
        f"Content-Type: {ctype}\r\n\r\n".encode()
        + data
        + f"\r\n--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(
        f"{API}/files",
        data=body,
        headers={"x-apikey": key, "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def report(label: str, stats: dict, name: str = "") -> int:
    bad = stats.get("malicious", 0) + stats.get("suspicious", 0)
    print(f"{label}: {'ЧИСТО' if bad == 0 else f'ДЕТЕКТЫ {bad}'} | {stats} | имя={name or '-'}")
    return 0 if bad == 0 else 1


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in ("file", "url"):
        print(__doc__)
        return 2
    mode, target = sys.argv[1], sys.argv[2]
    key = api_key()

    if mode == "url":
        uid = base64.urlsafe_b64encode(target.encode()).decode().rstrip("=")
        d = get(f"urls/{uid}", key)
        if "error" in d:
            print(f"URL не найден в VT: {d['error'].get('code')}")
            return 1
        a = d["data"]["attributes"]
        return report(target, a.get("last_analysis_stats", {}), a.get("title", ""))

    digest = hashlib.sha256(open(target, "rb").read()).hexdigest()
    d = get(f"files/{digest}", key)
    if "error" not in d:
        a = d["data"]["attributes"]
        return report(f"{os.path.basename(target)} sha256={digest[:16]}…", a.get("last_analysis_stats", {}), a.get("meaningful_name", ""))

    if "--upload" not in sys.argv:
        print(f"VT не знает файл {digest} (не значит «чисто»). Повторить с --upload:{os.path.basename(target)}")
        return 1

    up = upload(target, key)
    aid = up.get("data", {}).get("id")
    if not aid:
        print("Загрузка не удалась:", json.dumps(up)[:200])
        return 1
    print(f"загружено, analysis id {aid[:12]}…")
    for _ in range(10):
        time.sleep(15)
        r = get(f"analyses/{aid}", key)
        attrs = r.get("data", {}).get("attributes", {})
        if attrs.get("status") == "completed":
            return report(os.path.basename(target), attrs.get("stats", {}))
    print("Анализ не завершился за отведённое время — проверить позже")
    return 1


if __name__ == "__main__":
    sys.exit(main())
