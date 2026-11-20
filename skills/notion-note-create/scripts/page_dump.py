#!/usr/bin/env python3
"""page_dump.py — рекурсивный дамп блоков страниц Notion.

    python3 page_dump.py <page-id> [<page-id> ...]

Печатает заголовок, Тип1, дату правки и все блоки с типами;
`to_do` — с [x]/[ ], вложенные блоки — с отступом.
Нужен, чтобы 1) увидеть, что уже есть в соседней заметке, 2) проверить,
что созданная страница реально получила все блоки.
"""
import json, os, sys, urllib.request

TOK = open(os.path.expanduser("~/.hermes/state/.notion_token")).read().strip()
H = {"Authorization": f"Bearer {TOK}", "Notion-Version": "2026-03-11",
     "Content-Type": "application/json"}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60))


def rich(rt):
    return "".join(x.get("plain_text", "") for x in rt)


def dump(bid, depth=0, out=None):
    out = [] if out is None else out
    cursor = None
    while True:
        url = f"https://api.notion.com/v1/blocks/{bid}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        d = get(url)
        for b in d["results"]:
            t = b["type"]
            payload = b.get(t, {})
            txt = rich(payload.get("rich_text", []))
            if t == "to_do":
                txt = ("[x] " if payload.get("checked") else "[ ] ") + txt
            if txt.strip():
                out.append("  " * depth + f"<{t}> {txt}")
            if b.get("has_children"):
                dump(b["id"], depth + 1, out)
        if not d.get("has_more"):
            return out
        cursor = d.get("next_cursor")


for pid in sys.argv[1:]:
    p = get(f"https://api.notion.com/v1/pages/{pid}")
    title, t1 = "", None
    for v in p.get("properties", {}).values():
        if v.get("type") == "title":
            title = rich(v["title"])
        if v.get("type") == "select":
            t1 = (v.get("select") or {}).get("name")
    print("=" * 70)
    print(f"PAGE: {title} | Тип1: {t1} | {pid} | edited: {p.get('last_edited_time')}")
    print("=" * 70)
    blocks = dump(pid)
    for line in blocks:
        print(line)
    print(f"# blocks: {len(blocks)}")
