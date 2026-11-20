#!/usr/bin/env python3
"""Markdown (Gemini-транскрипт/саммари) -> страница конспекта в Notion.

Зачем: токен Notion умеет только читать и создавать — PATCH/DELETE блоков
отдают 403. Значит структуру надо строить СРАЗУ правильно: контент кладётся
внутрь toggles при создании/дозаписи в toggle, а не в page children.

Использование:
  python3 notion_md_blocks.py --title "Название видео" --url https://youtu.be/xxx \
      --summary /path/summary.md --transcript /path/transcript.md

Печатает URL созданной страницы. Требует ~/.hermes/state/.notion_token.
"""
import argparse
import json
import os
import re
import urllib.request

TOKEN_PATH = os.path.expanduser("~/.hermes/state/.notion_token")
DS = "63686c23-7a55-4126-95b3-93b9e49b9820"  # датасорс заметок (Тип1 = Конспект)
BATCH = 95  # Notion: не больше 100 блоков на запрос


def token():
    return open(TOKEN_PATH).read().strip()


def api(method, url, payload=None, tok=None):
    headers = {
        "Authorization": f"Bearer {tok or token()}",
        "Notion-Version": "2026-03-11",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def rt(text):
    return [{"type": "text", "text": {"content": text}}]


def clean(s):
    return s.replace("**", "").replace("__", "").replace("`", "").strip()


def md_to_blocks(md):
    """Markdown -> плоский список блоков Notion (paragraph/heading/bullet/divider)."""
    blocks, buf = [], []

    def flush():
        text = " ".join(buf).strip()
        while text:
            blocks.append({"object": "block", "type": "paragraph",
                           "paragraph": {"rich_text": rt(text[:1900])}})
            text = text[1900:]
        buf.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.lstrip().startswith("#"):
            flush()
            m = re.match(r"^(#{1,6})\s*(.+)$", line.lstrip())
            level = 1 if len(m.group(1)) == 1 else 2 if len(m.group(1)) == 2 else 3
            key = f"heading_{level}"
            blocks.append({"object": "block", "type": key, key: {"rich_text": rt(clean(m.group(2)))}})
            continue
        m = re.match(r"^\s*[-*+\u2022]\s+(.+)$", line)
        if m:
            flush()
            blocks.append({"object": "block", "type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text": rt(clean(m.group(1)))}})
            continue
        if line.strip() in ("---", "***"):
            flush()
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue
        buf.append(clean(line))
    flush()
    return blocks


def toggle(title, children):
    return {"object": "block", "type": "toggle",
            "toggle": {"rich_text": rt(title), "children": children[:BATCH]}}


def append(url, blocks):
    for i in range(0, len(blocks), BATCH):
        api("PATCH", url, {"children": blocks[i:i + BATCH]})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--transcript", required=True)
    a = p.parse_args()

    sum_blocks = md_to_blocks(open(a.summary).read())
    tr_blocks = md_to_blocks(open(a.transcript).read())

    page = api("POST", "https://api.notion.com/v1/pages", {
        "parent": {"data_source_id": DS},
        "properties": {
            "Название": {"title": rt(a.title)},
            "Тип1": {"select": {"name": "Конспект"}},
        },
        "children": [
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
                {"type": "text", "text": {"content": "🔗 Оригинал: "}},
                {"type": "text", "text": {"content": a.url, "link": {"url": a.url}}},
            ]}},
            toggle("📋 Саммари", sum_blocks),
            toggle("📝 Транскрибация", []),
        ],
    })
    pid = page["id"]
    toggles = api("GET", f"https://api.notion.com/v1/blocks/{pid}/children?page_size=100")["results"]
    sum_id = next(b["id"] for b in toggles if b["type"] == "toggle" and "Саммари" in b["toggle"]["rich_text"][0]["plain_text"])
    tr_id = next(b["id"] for b in toggles if b["type"] == "toggle" and "Транскрибация" in b["toggle"]["rich_text"][0]["plain_text"])

    # хвосты — внутрь СООТВЕТСТВУЮЩЕГО toggle, никогда в page children
    append(f"https://api.notion.com/v1/blocks/{sum_id}/children", sum_blocks[BATCH:])
    append(f"https://api.notion.com/v1/blocks/{tr_id}/children", tr_blocks)

    print("summary blocks:", len(sum_blocks), "transcript blocks:", len(tr_blocks))
    print("https://notion.so/" + pid.replace("-", ""))


if __name__ == "__main__":
    main()
