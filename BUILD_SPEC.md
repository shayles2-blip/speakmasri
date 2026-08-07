# 🎯 SpeakMasri — Complete Build Document
## English → Egyptian Arabic Learning Platform | Duolingo-Style MVP
### Multi-Agent Delivery System — Full Written Specification

---

## PART 1 — The Master Prompt (Copy-Paste Ready)

> Use this in any AI builder (v0, Cursor, Bolt, Lovable, Claude, ChatGPT) to generate the entire product.

```
Build a complete, single-file, runnable web application: a Duolingo-style
language-learning app called "SpeakMasri" as a FIRST MVP.

LANGUAGE PAIR (v1 only):
- FROM: English
- TO: Egyptian Arabic (spoken Masri dialect — NOT Modern Standard Arabic)
- All content authored as a FLUENT NATIVE EGYPTIAN SPEAKER would say it
  (real street phrases, never literal or AI-style translations)
- Every vocabulary item shown in THREE forms:
    1. English
    2. Arabic script (RTL)
    3. Franco-Arabic transliteration (e.g. "Ezzayak", "Shukran")

FEATURES (MVP):
1. Auth (signup/login, stored locally for single-file version)
2. Learning path: Units → Lessons → Exercises (winding node map like Duolingo)
3. Four exercise types:
   - Multiple choice translation
   - Match the pairs (English ↔ Arabic)
   - Listen & choose (audio via browser speech synthesis)
   - Fill in the blank
4. Gamification: XP points, daily streaks, hearts/lives (lose a heart on wrong answer)
5. Progress tracking (completed lessons unlock the next)
6. Leaderboard (top users by XP)
7. Profile page (XP, streak, logout)
8. Lesson-complete celebration screen with accuracy + XP earned

DESIGN:
- Match Duolingo's playful style
- Primary green #58cc02, blue #1cb0f6, red hearts #ff4b4b, yellow XP #ffc800
- Rounded corners, 3D "pressable" buttons (bottom shadow), Nunito font
- Mobile-first, max-width 480px, centered
- RTL support for Arabic text
- Owl mascot emoji 🦉, confetti 🎉 on success

TECH (single-file version):
- Pure HTML + CSS + vanilla JavaScript in ONE file (index.html)
- No backend, no npm, no build step
- Data persisted in localStorage
- Audio via built-in SpeechSynthesis API (Arabic voice)

DELIVER: one complete index.html file that runs by double-clicking.
```

---

## PART 2 — The Agent Fleet (Roles & Handoffs)

The product is built by 8 specialized agents, each with a clear role, input, and output.

```
1. DISCOVERY → 2. UX → 3. DESIGN → 4. DELIVERY →
5. CONTENT → 6. DEV → 7. TEST → 8. RELEASE
```

### 🔵 Agent 1 — Discovery (Product Manager)

**Role:** Define what to build and why.

**Problem Statement:**
English speakers struggle to learn *spoken* Egyptian Arabic. Existing apps teach Modern Standard Arabic (MSA) — formal, book-language nobody uses in daily Cairo life. There's a gap for authentic, native-authored dialect content.

**Target Personas:**

| Persona | Goal | Priority phrases |
|---|---|---|
| 🧳 Traveler "Sam" | Survive a trip to Egypt | greetings, prices, taxi, food |
| ❤️ Partner "Alex" | Talk to Egyptian in-laws | politeness, family, daily chat |
| 🌍 Heritage "Nour" | Reconnect with roots | conversation, culture |

**MVP Scope (MoSCoW):**
- **MUST:** Auth, learning path, 4 exercise types, XP/streak/hearts, native content, 3-form display (EN/AR/Franco), progress unlocking
- **SHOULD:** Leaderboard, profile, audio playback
- **WON'T (v1):** Stories, AI chatbot, multiple languages, social feed, payments

**Success Metrics (KPIs):**
- Day-1 retention > 40%
- Lesson completion rate > 60%
- Average streak > 3 days
- Time-to-first-lesson < 60 seconds

**User Stories (Gherkin):**
```gherkin
Feature: Complete a lesson
  Scenario: Learner finishes a lesson successfully
    Given I am logged in and viewing Unit 1
    When I answer all exercises
    Then I earn XP
    And my streak increments if it's a new day
    And the next lesson unlocks
    And I see a celebration screen

Feature: Hearts system
  Scenario: Learner answers incorrectly
    Given I am in a lesson with 5 hearts
    When I answer an exercise wrong
    Then I lose one heart
    And I see the correct answer

Feature: Streak
  Scenario: Daily return
    Given my last activity was yesterday
    When I complete a lesson today
    Then my streak increases by 1
```

### 🟣 Agent 2 — UX Research

**Role:** Map flows and the habit loop.

**Information Architecture:**
```
LANDING / AUTH
   └── MAIN
        ├── LEARN (path of units & lesson nodes)  ← default
        │      └── LESSON (exercises) → COMPLETE
        ├── LEADERBOARD
        └── PROFILE
```

**Core Learning Loop (Nir Eyal's Hook Model):**
```
TRIGGER    → streak reminder / open app
ACTION     → tap a lesson node, answer exercises
REWARD     → +XP, confetti, streak fire, unlock next node
INVESTMENT → streak grows (loss aversion keeps them returning)
```

**Lesson Flow:**
```
Tap node → Exercise 1 → (correct: green ✓ / wrong: red ✗, lose heart)
        → Exercise 2 → ... → Exercise N
        → Results screen (+XP, accuracy %) → back to path (next unlocked)
```

**Wireframe notes:**
- Top bar always shows: 🔥 streak · ⭐ XP · ❤️ hearts
- Learning path = vertical winding column of circular nodes (locked = gray, active = green, done = gold)
- Bottom nav = 🏠 Learn · 🏆 Leaderboard · 👤 Profile
- During lessons: progress bar at top, big "Check" button at bottom, feedback slides up from bottom

### 🟢 Agent 3 — Design (Visual System)

**Role:** Define the look & feel.

**Color Tokens:**

| Token | Hex | Use |
|---|---|---|
| Green | `#58cc02` | Primary, correct, active nodes |
| Green Dark | `#58a700` | Button bottom shadow |
| Blue | `#1cb0f6` | Selection, audio, links |
| Red | `#ff4b4b` | Hearts, errors |
| Yellow | `#ffc800` | XP, streak, completed nodes |
| Gray BG | `#f7f7f7` | Page background |
| Text | `#3c3c3c` | Body text |
| Border | `#e5e5e5` | Inputs, dividers |

**Typography:** Nunito (Latin) + Cairo/Tajawal (Arabic). Headings weight 900, buttons 800.

**Key Components:**
- **3D Button:** rounded 16px, `box-shadow: 0 4px 0 <dark>`, presses down on `:active` (translateY 4px, shadow removed)
- **Lesson node:** 70px circle, 6px bottom shadow, gray when locked / green when active / gold when done
- **Option button:** white with border; selected = blue tint; correct = green tint; wrong = red tint
- **Progress bar:** 16px tall, green fill, rounded
- **RTL:** Arabic text uses `direction: rtl` and Arabic font

**Layout:** mobile-first, `max-width: 480px`, centered, bottom nav fixed.

### 🟠 Agent 4 — Delivery (Tech Lead)

**Role:** Choose architecture & sequence the work.

**Architecture Decision:** For the MVP single-file version, everything is **one `index.html`** — HTML structure, CSS design system, vanilla JS logic, `localStorage` for data, and browser `SpeechSynthesis` for audio. No server needed. (A scaled version would split into React frontend + Node/Express + SQLite, but that's post-MVP.)

**Data Model (localStorage):**
```
lm_users   = [ {name, email, password, xp, streak, hearts, lastActive, progress:{lessonId:score}} ]
lm_current = email of logged-in user
```

**Screen State Machine:**
```
auth → main(learn|board|profile) → lesson → done → main
```

**Task Sequence:**
1. Content agent writes lessons (JS object)
2. Dev agent builds HTML/CSS/JS shell
3. Wire auth → path → lesson → complete
4. Add gamification (XP/streak/hearts)
5. Test agent validates flows
6. Release agent ships the file

### 🔴 Agent 5 — Content (Native Egyptian Author)

**Role:** Write authentic spoken Masri.

**Rules:**
- Real spoken Egyptian, NOT MSA, NOT literal translation
- Each item = { English, Arabic script, Franco transliteration }
- Prioritize what Egyptians actually say daily

**Content Set (as authored so far):**

**UNIT 1 — Greetings (التحيات)**

*Lesson 1-1: Hello & Hi (+10 XP)*

| English | Arabic | Franco |
|---|---|---|
| Hi (informal) | إزيك | Ezzayak |
| Welcome / Hey | أهلاً | Ahlan |
| Good morning | صباح الخير | Sabah el kheir |
| Good evening | مساء الخير | Masa el kheir |
| Goodbye | مع السلامة | Ma'a el salama |

*Lesson 1-2: How are you? (+10 XP)*

| English | Arabic | Franco |
|---|---|---|
| How are you? (to a man) | عامل إيه | 3amel eh |
| I'm good, thank God | الحمد لله كويس | El hamdulillah kwayes |
| Fine / OK | تمام | Tamam |
| Not good | مش كويس | Mesh kwayes |

**UNIT 2 — Politeness (الذوق)**

*Lesson 2-1: Please & Thanks (+10 XP)*

| English | Arabic | Franco |
|---|---|---|
| Thank you | شكراً | Shukran |
| You're welcome | عفواً | Afwan |
| Please (to a man) | لو سمحت | Law samaht |
| Sorry / Excuse me | آسف | Asef |
| Never mind / It's OK | معلش | Ma3lesh |

**UNIT 3 — Everyday Words (كلمات يومية)**

*Lesson 3-1: Yes, No & Common (+10 XP)*

| English | Arabic | Franco |
|---|---|---|
| Yes | أيوة | Aywa |
| No | لأ | La' |
| Let's go / Come on | يلا | Yalla |
| Finished / Enough / OK | خلاص | Khalas |
| God willing | *(cut off in source — content incomplete beyond this point)* |  |

---

## Status

This document was reconstructed from a shared spec/prompt pasted into chat; the source cut off mid-way through Unit 3, Lesson 3-1. Agents 6 (Dev), 7 (Test), and 8 (Release), and any content beyond the point above, were not included in the source and are not captured here.

**Not yet done:**
- Remaining Unit 3 content and any further units
- Actual `index.html` build (Agent 6/Dev)
- Test pass (Agent 7)
- Release/deploy (Agent 8) — including pointing `speakmasri.com` DNS at the deployed app
