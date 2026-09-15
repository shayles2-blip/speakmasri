#!/usr/bin/env python3
import os, sys, json, urllib.request, urllib.error

def krater_chat(prompt, model="qwen/qwen3.7-flash", system=None, max_tokens=4000):
    key = os.environ["KRATER_API_KEY"]
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(
        "https://api.krater.ai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]

def claude_chat(prompt, system=None, max_tokens=4000):
    key = os.environ["ANTHROPIC_API_KEY"]
    body = json.dumps({
        "model": "claude-opus-5",
        "max_tokens": max_tokens,
        **({"system": system} if system else {}),
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    return "".join(b["text"] for b in data["content"] if b["type"] == "text")

def chat(prompt, model="qwen/qwen3.7-flash", system=None, max_tokens=4000):
    """Try Krater first; fall back to Claude (claude-opus-5) if Krater errors or is down."""
    try:
        return krater_chat(prompt, model=model, system=system, max_tokens=max_tokens)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError, TimeoutError) as e:
        print(f"[krater_chat] Krater failed ({e}); falling back to Claude (claude-opus-5)", file=sys.stderr)
        return claude_chat(prompt, system=system, max_tokens=max_tokens)

if __name__ == "__main__":
    model = sys.argv[1]
    prompt = sys.stdin.read()
    print(chat(prompt, model=model))
