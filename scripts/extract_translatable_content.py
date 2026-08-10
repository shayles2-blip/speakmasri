#!/usr/bin/env python3
"""Extract English source copy from index.html for localization review."""

from __future__ import annotations

import ast
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "index.html"
OUTPUT = Path(__file__).with_name("translatable_content.json")


class JSLiteralParser:
    """Tiny parser for the JSON-like object/array literals used by COURSE."""

    def __init__(self, text: str, pos: int = 0):
        self.text, self.pos = text, pos

    def ws(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def value(self):
        self.ws()
        ch = self.text[self.pos]
        if ch == "{": return self.obj()
        if ch == "[": return self.array()
        if ch in "\"'": return self.string()
        m = re.match(r"-?\d+(?:\.\d+)?", self.text[self.pos:])
        if m:
            self.pos += len(m.group())
            return float(m.group()) if "." in m.group() else int(m.group())
        m = re.match(r"[A-Za-z_$][\w$]*", self.text[self.pos:])
        if not m: raise ValueError(f"Unexpected JS at offset {self.pos}")
        self.pos += len(m.group())
        return {"true": True, "false": False, "null": None}.get(m.group(), m.group())

    def string(self):
        quote, start = self.text[self.pos], self.pos
        self.pos += 1
        escaped = False
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            self.pos += 1
            if ch == quote and not escaped:
                raw = self.text[start:self.pos]
                try: return ast.literal_eval(raw)
                except (SyntaxError, ValueError):
                    return bytes(raw[1:-1], "utf-8").decode("unicode_escape")
            escaped = ch == "\\" and not escaped
            if ch != "\\": escaped = False
        raise ValueError("Unterminated JS string")

    def key(self):
        self.ws()
        return self.string() if self.text[self.pos] in "\"'" else self.identifier()

    def identifier(self):
        m = re.match(r"[A-Za-z_$][\w$]*", self.text[self.pos:])
        if not m: raise ValueError(f"Expected identifier at {self.pos}")
        self.pos += len(m.group())
        return m.group()

    def obj(self):
        out = {}; self.pos += 1
        while True:
            self.ws()
            if self.text[self.pos] == "}": self.pos += 1; return out
            key = self.key(); self.ws()
            if self.text[self.pos] != ":": raise ValueError(f"Expected colon at {self.pos}")
            self.pos += 1; out[key] = self.value(); self.ws()
            if self.text[self.pos] == ",": self.pos += 1; continue
            if self.text[self.pos] == "}": self.pos += 1; return out
            raise ValueError(f"Expected comma or closing brace at {self.pos}")

    def array(self):
        out = []; self.pos += 1
        while True:
            self.ws()
            if self.text[self.pos] == "]": self.pos += 1; return out
            out.append(self.value()); self.ws()
            if self.text[self.pos] == ",": self.pos += 1; continue
            if self.text[self.pos] == "]": self.pos += 1; return out
            raise ValueError(f"Expected comma or closing bracket at {self.pos}")


class ChromeParser(HTMLParser):
    SKIP = {"style", "script", "svg", "audio"}
    ATTRS = {"placeholder", "aria-label", "title"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.entries = [], []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.stack.append((tag, data))
        if not any(t in self.SKIP for t, _ in self.stack):
            for attr in self.ATTRS:
                if data.get(attr):
                    self.entries.append((data[attr], f"{attr} on {tag}", data.get("id", "")))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs); self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]; break

    def handle_data(self, data):
        if not self.stack or any(t in self.SKIP for t, _ in self.stack): return
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            tag, attrs = self.stack[-1]
            self.entries.append((text, f"visible text in {tag}", attrs.get("id", "")))


IMPORTANT_KEYS = {
    "Log In": "btn.login", "Sign Up": "btn.signup", "Log Out": "btn.logout",
    "Try a Lesson Free": "btn.try_lesson_free", "Check": "btn.check",
    "Continue": "btn.continue", "Learn": "nav.learn", "Phrasebook": "nav.phrasebook",
    "Profile": "nav.profile", "Translate:": "exercise.translate_prompt",
    "Listen and choose the meaning": "exercise.listen_prompt",
    "Type it in Franco-Arabic": "exercise.franco_prompt",
    "Match the pairs": "exercise.match_prompt", "Formal": "register.formal",
    "Casual": "register.casual", "Intimate": "register.intimate",
    "Base language": "settings.base_language", "Quit lesson": "aria.quit_lesson",
    "Email": "placeholder.email", "Your name": "placeholder.your_name",
}


def useful(text: str) -> bool:
    text = text.strip()
    return bool(text and not text.endswith("\\") and re.search(r"[A-Za-z]", text) and not re.search(r"[\u0600-\u06ff]", text)
                and text not in {"EN", "RU", "SpeakMasri"})


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return value[:52] or "string"


def js_strings(source: str):
    script = source[source.index("<script>") + 8:source.rindex("</script>")]
    patterns = [
        (r"(?:textContent|placeholder)\s*=\s*([\"'])(.*?)\1", "JavaScript text assignment"),
        (r"(?:alert|confirm)\(\s*([\"'])(.*?)\1", "dialog message"),
        (r"['\"](auth/[^'\"]+)['\"]\s*:\s*([\"'])(.*?)\2", "authentication error message"),
        (r"label\s*:\s*([\"'])(Formal|Casual|Intimate)\1", "register pill label"),
    ]
    for pattern, context in patterns:
        for m in re.finditer(pattern, script, re.S):
            value = m.group(3) if pattern.startswith("['\"](auth/") else m.group(2)
            value = value.replace("\\'", "'").replace('\\"', '"')
            if useful(value): yield value, context, ""

    # User-facing literal fragments inside templates/conditionals need explicit extraction.
    extras = [
        ("This email is already registered.", "authentication error message"),
        ("Incorrect password.", "authentication error message"),
        ("Invalid email or password.", "authentication error message"),
        ("Password should be at least 6 characters.", "authentication error message"),
        ("Please enter a valid email address.", "authentication error message"),
        ("No account found with this email.", "authentication error message"),
        ("Something went wrong. Please try again.", "authentication error message"),
        ("Copy this link to send your partner:", "copy-link prompt"),
        ("No moments yet — finish a lesson and try the mission tonight.", "empty moments message"),
        ("No partner phrases yet.", "empty partner-phrases message"),
        ("Delete phrase", "aria-label on delete button"),
        ("Nothing unlocked yet — finish your first lesson.", "empty phrasebook message"),
        ("Translate:", "multiple-choice exercise instruction"),
        ("Correct!", "positive exercise feedback"), ("Not quite", "incorrect exercise feedback"),
        ("Answer:", "answer reveal label"), ("Tonight's mission", "mission heading"),
        ("Say this to them:", "mission instruction"), ("I said it!", "mission completion button"),
        ("Finish", "rehearsal button"), ("Next", "rehearsal button"),
        ("Hear native pronunciation", "aria-label on audio button"),
        ("Hold to record yourself", "aria-label on recording button"),
        ("Mic access not available — just practice saying it out loud", "microphone fallback instruction"),
        ("All done!", "rehearsal completion heading"),
        ("You've practiced the whole lesson.", "rehearsal completion message"),
        ("Back to lessons", "rehearsal completion button"),
        ("Formal", "register pill label"), ("Casual", "register pill label"),
        ("Intimate", "register pill label"),
    ]
    yield from ((t, c, "") for t, c in extras)


def main():
    source = SOURCE.read_text(encoding="utf-8")
    marker = re.search(r"const\s+COURSE\s*=", source)
    if not marker: raise SystemExit("Could not find COURSE in index.html")
    parser = JSLiteralParser(source, marker.end())
    course = parser.value()

    vocab, lessons, units = [], [], []
    for unit in course["units"]:
        units.append({"id": unit["id"], "title": unit["title"]})
        for lesson in unit["lessons"]:
            lessons.append({"id": lesson["id"], "title": lesson["title"]})
            for idx, item in enumerate(lesson["vocab"]):
                vocab.append({"lessonId": lesson["id"], "idx": idx,
                              **{k: item.get(k, "") for k in ("en", "ar", "franco", "register")}})

    chrome = ChromeParser(); chrome.feed(source)
    raw = chrome.entries + list(js_strings(source))
    # The landing demo's Thank you is already vocab; the other two variants are standalone copy.
    raw += [("My love", "standalone landing-page demo phrase", ""),
            ("How are you", "standalone landing-page demo phrase", "")]
    seen_text, used_keys, ui = set(), set(), []
    for text, context, element_id in raw:
        text = html.unescape(re.sub(r"\s+", " ", text)).strip()
        if not useful(text) or text in seen_text: continue
        seen_text.add(text)
        key = IMPORTANT_KEYS.get(text)
        if not key:
            prefix = "msg" if any(x in context for x in ("message", "error", "dialog")) else "ui"
            if "placeholder" in context: prefix = "placeholder"
            if "aria-label" in context: prefix = "aria"
            if "landing-page demo" in context: prefix = "demo.phrase"
            key = f"{prefix}.{slug(element_id or text)}"
        base, n = key, 2
        while key in used_keys:
            key = f"{base}_{n}"; n += 1
        used_keys.add(key)
        ui.append({"key": key, "text": text, "context": context})

    result = {"vocab": vocab, "lessonTitles": lessons, "unitTitles": units, "uiStrings": ui}
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"vocab={len(vocab)} lessonTitles={len(lessons)} unitTitles={len(units)} uiStrings={len(ui)}")


if __name__ == "__main__":
    main()
