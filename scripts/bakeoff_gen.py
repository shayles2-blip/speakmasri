#!/usr/bin/env python3
import sys, os, json, urllib.request

SYSTEM = """You are a native-born Cairo Egyptian, a professional Egyptian Arabic (Masri) linguist and
language-course author with 15 years experience teaching foreigners spoken (not MSA/formal) Egyptian
Arabic. You know exactly what a real Cairo local says day-to-day, including natural slang, and you never
produce stiff textbook-Arabic or literal AI-style translations."""

PROMPT = """Author vocab for a lesson called "Family & Terms of Endearment" for the app SpeakMasri,
targeting someone learning Masri to talk with their Egyptian partner and in-laws.

Output STRICT JSON only, an array of exactly 6 objects, no prose, no markdown fences:
[{"en":"...","ar":"...","franco":"..."}]

Each "ar" must be real Egyptian Arabic script. Each "franco" must be natural Franco-Arabic (as Egyptians
actually text: 3 for ع, 7 for ح, 2 for ء where natural). Cover: a term of endearment, addressing
mother/father-in-law respectfully, "I love you" (as actually said, not textbook), asking about family,
and 2 more items a partner would realistically need in the first month with the family."""

def call(model, max_tokens):
    key = os.environ["KRATER_API_KEY"]
    body = json.dumps({
        "model": model,
        "messages": [{"role":"system","content":SYSTEM},{"role":"user","content":PROMPT}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        "https://api.krater.ai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=280) as resp:
        return json.load(resp)

def main():
    model = sys.argv[1]
    for max_tokens in (6000, 14000):
        try:
            d = call(model, max_tokens)
        except Exception as e:
            print(json.dumps({"error": f"request failed: {e}"}))
            return
        choice = d.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content")
        if content:
            print(content.strip())
            return
    print(json.dumps({"error": "empty content after retry", "raw": json.dumps(d)[:500]}))

if __name__ == "__main__":
    main()
