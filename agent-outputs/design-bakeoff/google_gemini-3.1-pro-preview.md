As a Senior Product Designer, my approach here is to mature the visual language. The current design uses a "Neubrutalist/Arcade" style (heavy solid drop shadows, neon colors, bouncy Y-axis motion, rounded childish fonts). This works for a kid's game, but SpeakMasri is a relationship tool for adults connecting with their partner’s culture and family. It needs to feel intimate, culturally respectful, premium, and trustworthy.

We will keep the energetic green brand anchor, but shift the execution from "cheap arcade" to "crafted iOS-native experience."

Here is the precise design specification to elevate SpeakMasri.

### 1. The Refined Palette (The "Nile Oasis" Theme)
We are shifting the neon `#58cc02` to a richer, more sophisticated **Emerald/Oasis Green**. We’ll support it with warm, alabaster neutrals that nod to Egyptian landscapes, rather than sterile clinical grays. 

*   **Primary Brand (Green)**
    *   `--primary: #1DA14A;` *(A sophisticated, rich green. Vibrant, but easier on the eyes than the previous neon)*
    *   `--primary-hover: #16823A;` *(Deep green for interaction states)*
    *   `--primary-surface: #EAF5ED;` *(A very soft, premium green tint for selected states/feedback)*
*   **Accents (Replacing the generic cyan/yellow)**
    *   `--accent-gold: #D4AF37;` *(A rich Egyptian gold for achievements/streaks, replacing the cheap `#ffc800`)*
    *   `--error: #D94541;` *(A warm terracotta/clay red, replacing the glaring neon `#ff4b4b`)*
    *   `--error-surface: #FFF0EE;`
*   **Neutrals & Canvas**
    *   `--bg-canvas: #FCFBFA;` *(A warm "Alabaster" off-white, making the app feel intimate and premium)*
    *   `--surface: #FFFFFF;` *(Pure white for cards to pop against the canvas)*
    *   `--text-main: #1C2024;` *(Deep ink, never pure black)*
    *   `--text-muted: #687076;` *(For Franco-Arabic translations and subtitles)*
    *   `--border-light: #E6E8EB;`

### 2. Typography
We are completely dropping **Nunito**. It is highly associated with elementary education apps. 
*   **English/Latin:** **`Plus Jakarta Sans`** (Google Fonts). It is geometric, highly legible, but has a sharp, premium humanist quality (similar to the font used by Stripe or modern fintech apps).
*   **Arabic:** Keep **`Tajawal`** (Google Fonts), but utilize its weights properly. It pairs beautifully with Plus Jakarta Sans.
*   **Hierarchy execution:**
    *   Headings (`h1`, `h2`): Plus Jakarta Sans, `ExtraBold` (800), tight letter spacing (`-0.02em`).
    *   Body/Options: Plus Jakarta Sans, `SemiBold` (600).
    *   Arabic Text (`.ar`): Tajawal, `Bold` (700).

### 3. Component Philosophy & Motion
We are replacing the "chunky 3D block" aesthetic with a "tactile, floating surface" philosophy.

*   **Buttons:** Remove the solid 4px Y-offset shadow. Replace it with a smooth pill shape, a subtle optical shadow, and a scale-down press animation. This feels like high-end iOS UI.
*   **Cards & Options (`.opt`):** Instead of thick 2px borders that turn neon, we use delicate 1.5px borders. When selected, the border turns Primary Green, the background gets a soft tint (`--primary-surface`), and we rely on elegant checkmarks.
*   **The Path:** Drop the 70px bouncing bubbles. We will use a sleek, minimal timeline. A thin, continuous vertical line (`#E6E8EB`, 2px wide) connects elegant 56px circular nodes. Unlocked nodes are pristine white with a green stroke; completed nodes are solid green; locked nodes are muted. 
*   **Motion:** Shift from positional movement (`translateY`) to scale movement. It feels significantly more expensive. 

---

### 4. The Exact CSS Specifications (To be implemented)

Here are the concrete values and updated CSS to drop directly into your system:

```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Tajawal:wght@500;700;800&display=swap');

:root {
  /* Refined Palette */
  --primary: #1DA14A;
  --primary-hover: #16823A;
  --primary-surface: #EAF5ED;
  --accent-gold: #D4AF37;
  --error: #D94541;
  --error-surface: #FFF0EE;
  
  --bg-canvas: #FCFBFA;
  --surface: #FFFFFF;
  --text-main: #1C2024;
  --text-muted: #687076;
  --border-light: #E6E8EB;
  
  /* Precision Radii & Shadows */
  --r-sm: 12px;
  --r-md: 16px;
  --r-pill: 999px;
  --shadow-float: 0 8px 24px rgba(29, 161, 74, 0.12);
  --shadow-card: 0 2px 8px rgba(28, 32, 36, 0.04);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: 'Plus Jakarta Sans', sans-serif;
  -webkit-font-smoothing: antialiased;
}

body {
  background: var(--bg-canvas);
  color: var(--text-main);
}

.ar {
  font-family: 'Tajawal', sans-serif;
  direction: rtl;
  unicode-bidi: isolate;
  font-size: 1.1em; /* Arabic usually needs a slight optical bump */
}

/* ===== ELEVATED BUTTONS ===== */
.btn {
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: var(--r-pill); /* Pill shapes feel more premium here */
  padding: 16px 24px;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 0.5px;
  cursor: pointer;
  width: 100%;
  transition: transform 0.15s cubic-bezier(0.4, 0, 0.2, 1), background 0.15s;
  box-shadow: var(--shadow-float);
}

.btn:active {
  transform: scale(0.96); /* Scale down instead of chunky Y-drop */
  background: var(--primary-hover);
}

.btn:disabled {
  background: var(--border-light);
  color: #A0AAB2;
  box-shadow: none;
  cursor: not-allowed;
  transform: none;
}

.btn-ghost {
  background: var(--surface);
  color: var(--text-main);
  border: 1.5px solid var(--border-light);
  box-shadow: var(--shadow-card);
}

/* ===== REFINED EXERCISE CARDS ===== */
.opt {
  display: block;
  width: calc(100% - 32px);
  margin: 10px 16px;
  padding: 20px;
  border: 1.5px solid var(--border-light);
  border-radius: var(--r-md);
  background: var(--surface);
  cursor: pointer;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-card);
}

.opt:active {
  transform: scale(0.98);
}

/* Premium Selection & Feedback States */
.opt.sel {
  border-color: var(--primary);
  background: var(--primary-surface);
  color: var(--primary-hover);
}

.opt.correct {
  border-color: var(--primary);
  background: var(--primary-surface);
  color: var(--primary-hover);
  /* Replaced cheap neon green with elegant tinted surface */
}

.opt.wrong {
  border-color: var(--error);
  background: var(--error-surface);

