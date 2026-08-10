#!/usr/bin/env python3
"""Generate Russian localization review data through the Krater API."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE / "translatable_content.json"
OUTPUT = HERE / "translatable_content_ru.json"
ENDPOINT = "https://api.krater.ai/v1/chat/completions"

SYSTEM = """You are a native Russian speaker who personally learned Egyptian Arabic (Masri) to communicate with your Egyptian partner's family. You write natural, warm, idiomatic Russian — never stiff textbook translation, never word-for-word literal rendering. You understand that this app teaches REAL spoken Egyptian Arabic (not formal Modern Standard Arabic), and your Russian explanations should match that same authentic, practical, real-life register — as if you're personally explaining these phrases to a Russian friend who's about to meet their Egyptian in-laws."""


def call(model: str, prompt: str, max_tokens: int):
    key = os.environ["KRATER_API_KEY"]
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=280) as resp:
        return json.load(resp)


def request_json(model: str, prompt: str):
    last = None
    for max_tokens in (6000, 14000):
        try:
            response = call(model, prompt, max_tokens)
        except Exception as exc:
            last = f"request failed: {exc}"
            continue
        content = response.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            last = "empty content"
            continue
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            if text.lstrip().startswith("json"): text = text.lstrip()[4:].lstrip()
        try:
            value = json.loads(text)
            if not isinstance(value, list): raise ValueError("top level is not an array")
            return value
        except Exception as exc:
            last = f"invalid JSON: {exc}"
    raise RuntimeError(last or "empty content after retry")


def chunks(items, size):
    for start in range(0, len(items), size):
        yield start // size + 1, items[start:start + size]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {Path(sys.argv[0]).name} MODEL")
    model = sys.argv[1]
    source = json.loads(INPUT.read_text(encoding="utf-8"))
    result = json.loads(json.dumps(source, ensure_ascii=False))
    failed = {"vocab": 0, "lessonTitles": 0, "unitTitles": 0, "uiStrings": 0}

    for batch_no, batch in chunks(source["vocab"], 18):
        prompt = """Translate each English `en` value into natural Russian. Preserve its formal/casual/intimate/neutral register and translate every parenthetical usage note without dropping it. Arabic and Franco-Arabic are context, not text to translate. Return STRICT JSON only, no markdown or prose, exactly one result per input in this shape: [{\"lessonId\":\"...\",\"idx\":0,\"ru\":\"...\"}].\n\nINPUT:\n""" + json.dumps(batch, ensure_ascii=False)
        try:
            translated = request_json(model, prompt)
            lookup = {(x.get("lessonId"), x.get("idx")): x.get("ru") for x in translated}
            for item in result["vocab"]:
                value = lookup.get((item["lessonId"], item["idx"]))
                if isinstance(value, str) and value.strip(): item["ru"] = value.strip()
            missing = sum((x["lessonId"], x["idx"]) not in lookup for x in batch)
            failed["vocab"] += missing
            print(f"vocab batch {batch_no}: {len(batch)-missing}/{len(batch)} translated")
        except Exception as exc:
            failed["vocab"] += len(batch)
            print(f"ERROR vocab batch {batch_no}: {exc}", file=sys.stderr)

    for category in ("lessonTitles", "unitTitles"):
        batch = source[category]
        prompt = """Translate these course titles into concise, appealing, natural Russian. Retain any Egyptian Arabic/Arabic-script wording where it is pedagogically useful. Return STRICT JSON only, no markdown or prose, exactly one result per input: [{\"id\":\"...\",\"title_ru\":\"...\"}].\n\nINPUT:\n""" + json.dumps(batch, ensure_ascii=False)
        try:
            translated = request_json(model, prompt)
            lookup = {x.get("id"): x.get("title_ru") for x in translated}
            for item in result[category]:
                value = lookup.get(item["id"])
                if isinstance(value, str) and value.strip(): item["title_ru"] = value.strip()
            missing = sum(x["id"] not in lookup for x in batch)
            failed[category] += missing
            print(f"{category}: {len(batch)-missing}/{len(batch)} translated")
        except Exception as exc:
            failed[category] += len(batch)
            print(f"ERROR {category}: {exc}", file=sys.stderr)

    for batch_no, batch in chunks(source["uiStrings"], 25):
        prompt = """Translate each UI string into natural, concise Russian copy for a phone app. Use its context to choose the right wording; do not translate mechanically. Preserve placeholders, punctuation, emoji, and interpolation-like fragments. Never translate or alter the brand name \"SpeakMasri\" - keep it exactly as-is wherever it appears. Return STRICT JSON only, no markdown or prose, exactly one result per input: [{\"key\":\"...\",\"ru\":\"...\"}].\n\nINPUT:\n""" + json.dumps(batch, ensure_ascii=False)
        try:
            translated = request_json(model, prompt)
            lookup = {x.get("key"): x.get("ru") for x in translated}
            for item in result["uiStrings"]:
                value = lookup.get(item["key"])
                if isinstance(value, str) and value.strip(): item["ru"] = value.strip()
            missing = sum(x["key"] not in lookup for x in batch)
            failed["uiStrings"] += missing
            print(f"uiStrings batch {batch_no}: {len(batch)-missing}/{len(batch)} translated")
        except Exception as exc:
            failed["uiStrings"] += len(batch)
            print(f"ERROR uiStrings batch {batch_no}: {exc}", file=sys.stderr)

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    for category in failed:
        total = len(source[category]); print(f"{category}: translated={total-failed[category]} failed={failed[category]}")


if __name__ == "__main__":
    main()
