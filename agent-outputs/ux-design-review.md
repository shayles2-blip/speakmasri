**Scope note:** JS is cut at `const COURSE=` — everything below is from the visible HTML/CSS. Items marked ⚠️ need the truncated logic verified.

## 1. UX bugs actually in the code

- **`.feedback{position:fixed;bottom:0}` covers the Check button.** `#checkBtn` sits in normal flow at the bottom of `#lesson`; the feedback sheet is fixed over it. After answering, the user can't reach Continue. Fix: move the primary button *inside* `.feedback`, and give `#lesson` `padding-bottom:180px`.
- **Hearts are hardcoded in markup**: `<span id="hearts">5</span>` and `<span id="lHearts">5</span>`. On reload the header lies until first re-render. Render both from state on boot. ⚠️ Also no zero-hearts screen, no refill/timer anywhere in CSS or HTML → dead-end state.
- **Auth screen is a triple-guess form.** One `#name` field labelled "Name (for signup)" plus two equal-weight buttons (`Sign Up`, `Log In`). No `<form>`, so no Enter-to-submit, no `autocomplete` attrs. Split into two modes with a text toggle; wrap in `<form onsubmit>`.
- **✕ quit button** (`onclick="quitLesson()"`) is a bare 24px glyph, ~24×24px tap target, no confirm dialog. Add `padding:10px;min-width:44px;min-height:44px` + "Quit? You'll lose progress" confirm.
- **`.app{min-height:100vh}` + `position:fixed` nav** = the classic iOS Safari bug: nav hides under the toolbar/home bar. Use `100dvh` and add `padding-bottom:env(safe-area-inset-bottom)` to `.nav` and `.feedback`.
- **`.node.o2{margin-left:80px}`** shifts layout, so the `.ltitle` (width:120px) no longer aligns under its node. Use `transform:translateX(80px)` on a node+title wrapper instead.
- **No `:focus-visible` rule anywhere.** Keyboard users get zero affordance on `.opt`, `.node`, `.nav button`. Add `:focus-visible{outline:3px solid #1cb0f6;outline-offset:2px}`.

## 2. Spec ↔ implementation mismatches

- **Fonts never loaded.** `*{font-family:'Nunito'…}` and `.ar{font-family:'Cairo','Tajawal'}` with no `<link>`/`@font-face`. Spec says Nunito; you ship Segoe UI. Add the Google Fonts link (Nunito 400/700/800 + Cairo).
- **Celebration screen mislabels XP.** `#dXp` placeholder is `+10` but the caption reads "Total XP". Spec asks for *XP earned*. Change caption to "XP Earned".
- **"Time-to-first-lesson < 60s" KPI vs. a hard auth wall** as screen 1. Add a "Try a lesson first" guest button; gate signup at lesson-complete.
- **Leaderboard is fiction.** `#lbList` in a localStorage-only app = seeded fake users. Either label it "Practice League (demo)" or cut it; spec ranks it SHOULD, not MUST.
- ⚠️ **Streak spec ("increments if it's a new day")** — no timezone/last-active handling visible, and no streak-at-risk UI. Avg-streak >3 days won't happen without a reminder surface.

## 3. RTL / a11y

- **Arabic has no `lang`.** `<html lang="en">` and `.ar` sets only `direction:rtl`. Screen readers/TTS read Arabic with an English voice. Add `lang="ar-EG"` + `unicode-bidi:isolate` on `.ar`; use `dir="auto"` on the fill-in-blank input (`.fillwrap input` is LTR + centered — Arabic typed next to "___" will reorder visibly).
- ⚠️ **SpeechSynthesis has no `ar` voice on most desktops.** "Listen & choose" silently fails. Filter `voices.find(v=>v.lang.startsWith('ar'))`; if none, disable `.audio-btn` and swap that exercise type.
- **Correct/wrong is color-only** (`.fb-ok`/`.fb-no`, `.opt.correct/.wrong`) — WCAG 1.4.1 fail. Add ✓/✕ glyphs + `role="status" aria-live="polite"` on `#fbArea`; `role="alert"` on `#authErr`.
- **Contrast failures:** `.franco{color:#999}` = 2.8:1 (and 13px italic — this is the *primary* learning cue); `.rank{color:var(--yellow)}` = 1.7:1, effectively invisible; white on `--green` `.btn` = 2.4:1.
- **Emoji-only nav** (`🏠🏆👤`) with no `aria-label`, and active state = a 3px border color. Add labels + text captions + `aria-selected`.
- `.progbar` needs `role="progressbar" aria-valuenow`. `tab()`/next-exercise need focus moved to the new `<h2>`/`.q`.

## 4. Top 5 fixes, ranked

1. **Un-bury the Check button** — nest `#checkBtn` inside `.feedback`; add `#lesson{padding-bottom:180px}`. Blocks lesson completion = blocks the 60% completion KPI.
2. **Hearts: render from state + build the zero-hearts screen** with a refill path (practice or 30-min timer). Currently an unrecoverable dead end.
3. **Load Nunito + Cairo, set `lang="ar-EG"`/`unicode-bidi:isolate` on `.ar`, `dir="auto"` on the fill input.** Fixes brand *and* bidi correctness in one pass.
4. **Contrast + size pass:** `.franco` → `#6b6b6b`, 15px, non-italic; `.rank` → `#b98600`; `.btn` → `background:#46a302;font-size:18px`.
5. **Guest-first onboarding:** "Try a lesson