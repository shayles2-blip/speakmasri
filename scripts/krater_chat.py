#!/usr/bin/env python3
import os, sys, json, urllib.request

def chat(prompt, model="qwen/qwen3.7-flash", system=None, max_tokens=4000):
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

if __name__ == "__main__":
    model = sys.argv[1]
    prompt = sys.stdin.read()
    print(chat(prompt, model=model))
