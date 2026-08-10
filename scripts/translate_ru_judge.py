#!/usr/bin/env python3
"""Flag questionable Russian localization entries through an independent model."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE / "translatable_content_ru.json"
OUTPUT = HERE / "translatable_content_ru_flagged.json"
ENDPOINT = "https://api.krater.ai/v1/chat/completions"
SYSTEM = """You are a native Russian speaker, ruthless quality-control judge. You are shown Russian translations of Egyptian-Arabic-learning-app content. Flag any entry that reads as stiff, literal, robotic, unnatural, or wrong-register Russian. You do not write corrections - you only flag problems with a short reason, so a human reviewer can fix them."""


def call(model, prompt, max_tokens):
    key = os.environ["KRATER_API_KEY"]
    body = json.dumps({"model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=280) as resp: return json.load(resp)


def request_json(model, prompt):
    last = None
    for max_tokens in (6000, 14000):
        try: response = call(model, prompt, max_tokens)
        except Exception as exc: last = f"request failed: {exc}"; continue
        content = response.get("choices", [{}])[0].get("message", {}).get("content")
        if not content: last = "empty content"; continue
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines(); text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            if text.lstrip().startswith("json"): text = text.lstrip()[4:].lstrip()
        try:
            value = json.loads(text)
            if not isinstance(value, list): raise ValueError("top level is not an array")
            return value
        except Exception as exc: last = f"invalid JSON: {exc}"
    raise RuntimeError(last or "empty content after retry")


def chunks(items, size=22):
    for start in range(0, len(items), size): yield start // size + 1, items[start:start + size]


def main():
    if len(sys.argv) != 2: raise SystemExit(f"Usage: {Path(sys.argv[0]).name} MODEL")
    model = sys.argv[1]
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    review = []
    for item in data["vocab"]:
        if item.get("ru"):
            review.append({"identifier": f"{item['lessonId']}+{item['idx']}", "kind": "vocab", **item})
    for category in ("lessonTitles", "unitTitles"):
        for item in data[category]:
            if item.get("title_ru"):
                review.append({"identifier": f"{category}:{item['id']}", "kind": category, **item})
    for item in data["uiStrings"]:
        if item.get("ru"):
            review.append({"identifier": item["key"], "kind": "uiString", **item})

    flagged, failed_batches = [], 0
    for batch_no, batch in chunks(review):
        prompt = """Review every Russian translation against its English source and context. Flag only genuine quality problems: stiff, literal, robotic or unnatural Russian, semantic errors, dropped usage notes, or wrong register. Do NOT suggest corrections. Return STRICT JSON only, no markdown or prose, as an array containing only problems (or []): [{\"key or lessonId+idx\":\"identifier copied exactly from input\",\"issue\":\"short reason in Russian or English\"}].\n\nINPUT:\n""" + json.dumps(batch, ensure_ascii=False)
        try:
            found = request_json(model, prompt)
            for entry in found:
                ident = entry.get("key or lessonId+idx")
                issue = entry.get("issue")
                if isinstance(ident, str) and isinstance(issue, str) and ident and issue:
                    flagged.append({"key or lessonId+idx": ident, "issue": issue})
            print(f"batch {batch_no}: reviewed={len(batch)} flagged={len(found)}")
        except Exception as exc:
            failed_batches += 1
            print(f"ERROR judge batch {batch_no}: {exc}", file=sys.stderr)
    OUTPUT.write_text(json.dumps(flagged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"reviewed={len(review)} flagged={len(flagged)} failed_batches={failed_batches}")


if __name__ == "__main__": main()
