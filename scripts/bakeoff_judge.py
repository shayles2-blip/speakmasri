#!/usr/bin/env python3
import sys, os, json, urllib.request

SYSTEM = """You are a native-born Cairo Egyptian, ruthless dialect-authenticity QA judge for a language
app. You are shown several anonymous submissions (labeled A, B, C...) each authoring the same lesson.
Score each PURELY on how authentic and natural real spoken Cairo Egyptian Arabic (Masri) sounds - not
Modern Standard Arabic, not textbook, not stiff. Penalize any MSA-isms, awkward literal translation, or
wrong register heavily. You do not know which AI model produced which submission - judge blind."""

def build_prompt(submissions):
    parts = ["Score each submission 1-10 for Masri authenticity. Output STRICT JSON only, no markdown "
             "fences, no prose outside the JSON, in this exact shape:\n"
             '{"scores":[{"label":"A","score":7,"note":"one short reason"}, ...],"best":"<label of the best one>"}\n\n']
    for s in submissions:
        parts.append(f"=== Submission {s['label']} ===\n{s['text']}\n")
    return "\n".join(parts)

def call(model, prompt, max_tokens):
    key = os.environ["KRATER_API_KEY"]
    body = json.dumps({
        "model": model,
        "messages": [{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        "https://api.krater.ai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=280) as resp:
        return json.load(resp)

def main():
    judge_model = sys.argv[1]
    submissions_path = sys.argv[2]
    submissions = json.load(open(submissions_path))
    prompt = build_prompt(submissions)
    for max_tokens in (6000, 14000):
        try:
            d = call(judge_model, prompt, max_tokens)
        except Exception as e:
            print(json.dumps({"error": f"request failed: {e}"}))
            return
        choice = d.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content")
        if content:
            print(content.strip())
            return
    print(json.dumps({"error": "empty content after retry"}))

if __name__ == "__main__":
    main()
