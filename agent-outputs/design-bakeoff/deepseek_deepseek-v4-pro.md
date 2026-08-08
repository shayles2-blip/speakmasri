**SpeakMasri · Premium Design System**

Below is a decisive, implementation-ready system that transforms the current “cartoon” green aesthetic into a polished, confident brand while keeping your anchor colour. Everything is specified exactly so your developers can copy‑paste the tokens and class structures.

---

## 1. Refined Palette

Retiring the hyper‑neon `#58cc02` in favour of a deeper, more sophisticated green that still feels fresh and unmistakably SpeakMasri. The new palette is calm, high‑contrast, and prints well on both light and dark backgrounds.

### Core colours (CSS custom properties)
```css
:root {
  /* Primary green family */
  --green-400: #7BCC4A;   /* light tint, used for hover states, subtle backgrounds */
  --green-500: #4B9C2E;   /* PRIMARY solid – replaces #58cc02 */
  --green-600: #3A7E24;   /* dark shade – used for pressed states, text on light bg */
  --green-700: #2C5F1A;   /* deep shadow accent */

  /* Neutral palette */
  --neutral-0: #FFFFFF;
  --neutral-50: #F8FAFC;  /* page background */
  --neutral-100: #F1F5F9; /* card secondary background */
  --neutral-200: #E2E8F0; /* subtle borders */
  --neutral-300: #CBD5E1; /* interactive borders */
  --neutral-500: #64748B; /* secondary text, icons */
  --neutral-800: #1E293B; /* primary text */
  --neutral-900: #0F172A; /* headings */

  /* Accent – refined from the original Duolingo‑bright tones */
  --blue-500: #0D86C4;    /* actionable, audio, links – calmer than #1cb0f6 */
  --red-500: #E53935;     /* error – a touch more elegant than #ff4b4b */
  --amber-500: #F59E0B;   /* completion, “done” nodes – warmer than #ffc800 */

  /* Radius & spacing (8px scale) */
  --radius-sm: 12px;
  --radius-md: 16px;
  --radius-lg: 20px;
  --radius-full: 9999px;

  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;

  /* Shadows – soft, layered, no 3‑D “pop‑off” effect */
  --shadow-xs: 0 1px 2px 0 rgba(0,0,0,0.05);
  --shadow-sm: 0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.06), 0 2px 4px -2px rgba(0,0,0,0.05);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
}
```

**Why these choices**  
- `--green-500` sits at ≈ 91° hue (yellow‑green family), but with 70% saturation and 40% lightness – vibrant yet grounded.  
- Neutrals lean towards cool grays (`#F8FAFC`, `#E2E8F0`) to feel crisp and modern, avoiding the “muddy” warmth of old `#e5e5e5`.  
- Accents (`blue`, `red`, `amber`) are slightly desaturated so they don’t scream “edtech for kids”.

---

## 2. Typography

Move away from the over‑familiar Nunito to a contemporary geometric‑humanist blend. Headings use **Outfit** (soft, slightly wide, highly legible), body and UI labels use **Inter** (excellent readability at small sizes). Both are Google Fonts that load instantly.

```css
/* Google Fonts import */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400..600&family=Outfit:wght@500;600;700;800&display=swap');

:root {
  --font-display: 'Outfit', system-ui, -apple-system, sans-serif;
  --font-body: 'Inter', system-ui, -apple-system, sans-serif;
  --font-arabic: 'Cairo', 'Tajawal', sans-serif; /* retained, injected via .ar class */
}

body {
  font-family: var(--font-body);
  color: var(--neutral-800);
  font-size: 16px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3, .brand, .btn, .unit-head, .q {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: -0.02em;
}

/* Adjust Arabic elements */
.ar {
  font-family: var(--font-arabic);
  direction: rtl;
  unicode-bidi: isolate;
}
```

**Specific usage**  
- **Logo / Brand name**: `Outfit 800`, 36px, letter-spacing -0.03em, colour `--green-600`.  
- **Headings** (`.unit-head`, `.q`): `Outfit 700`, 22px / 28px (mobile default).  
- **Buttons**: `Outfit 600`, 16px, normal sentence case (no uppercasing).  
- **Body / input text**: `Inter 400/500`, 16px.  
- **Arabic tab**: Inherits via `.ar` class – Cairo already matches well.

---

## 3. Component Philosophy & Concrete Specs

All components follow three premium rules:  
- **Subtle elevation** (soft shadows, never harsh 4–6px block offsets).  
- **Generous whitespace** (24‑32px minimum padding on cards).  
- **State feedback via colour fill + micro‑interaction**, not popup banners.

### 3.1 Buttons

```css
.btn {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1rem;
  padding: var(--space-2) var(--space-3);   /* 16px 24px */
  border-radius: var(--radius-md);          /* 16px */
  border: none;
  cursor: pointer;
  text-transform: none;                     /* NO MORE ALL CAPS */
  letter-spacing: -0.01em;
  transition: all var(--transition-base);   /* background, shadow, transform */

  /* Layered flat design with a subtle gradient and soft shadow */
  background: linear-gradient(135deg, var(--green-500) 0%, var(--green-600) 100%);
  color: white;
  box-shadow: var(--shadow-sm);

  /* No horizontal movement on press – just a subtle scale & deeper shadow */
  &:active {
    transform: scale(0.98);
    box-shadow: var(--shadow-xs);
    background: var(--green-600);           /* solid dark for press */
  }

  &:disabled {
    background: var(--neutral-200);
    color: var(--neutral-500);
    box-shadow: none;
    cursor: not-allowed;
    transform: none;
  }
}

/* Blue (audio / secondary action) */
.btn-blue {
  background: linear-gradient(135deg, var(--blue-500) 0%, #0B76A8 100%);
  box-shadow: var(--shadow-sm);
  /* same press behaviour */
}

/* Ghost / outline */
.btn-ghost {
  background: transparent;
  color: var(--green-600);
  border: 2px solid var(--neutral-300);
  box-shadow: none;
  &:active {
    background: var(--green-400);
    border-color: var(--green-500);
    color: white;
    transform: scale(0.98);
  }
}
```

**Audio button** – keep the round `80px` circle but use the blue gradient and a soft `shadow-md`, plus an inner glow on press (using `box-shadow: inset 0 2px 4px rgba(0,0,0,0.1)`).

### 3.2 Cards & Containers

All panels become “cards” with generous radius and soft shadows.

```css
.card {
  background: var(--neutral-0);
  border-radius: var(--radius-lg);   /* 20px */
  padding: var(--space-3);           /* 24px */
  box-shadow: var(--shadow-md);
  margin: var(--space-2);            /* 16px gutter */
  border: 1px solid var(--neutral-100); /* subtle definition, separates from background */
}
```

**Specific overrides for existing screens:**  
- **`.unit-head`** – no longer a solid green block. Style as a card with a left green border accent (`border-left: 4px solid var(--green-500)`) and slightly transparent green background (`background: var(--green-400)` with 10% opacity). Text dark green, bold.  
- **Feedback (`#feedback`)** – transform into a floating toast at the top of the viewport (not bottom). Use `position: fixed; top: 20px; left: 50%; transform: translateX(-50%)` with `max-width: calc(100% - 48px)`, a white card with `shadow-lg`, a small coloured strip on the left (green for success, red for error), and a close icon. Auto‑dismiss after 2 seconds with a fade animation.

### 3.3 The Learning Path – From Bubble Nodes to a Premium Timeline

The current floating bubble path screams “game levels”. Replace it with a clean, vertically connected timeline that feels more like a guided curriculum.

**Structure** (HTML can be refactored but here’s the CSS):
```css
.path {
  display: flex;
  flex-direction: column;
  align-items: flex-start;               /* align to left */
  padding: var(--space-3) var(--space-2);
  gap: var(--space-1);
  position: relative;
  padding-left: 44px;                    /* room for the node + line */
}

.path::before {
  content: '';
  position: absolute;
  left: 24px;                            /* centre of node (node width 40px /2 + offset) */
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--neutral-200);
  z-index: 0;
}

.path-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  position: relative;
  z-index: 1;
  /* offset classes .o2, .o3 removed – no more zig‑zag */
}

.node {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);       /* 12px, almost square – feels refined */
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--green-500);
  color: white;
  font-size: 18px;
  font-weight: 700;
  box-shadow: var(--shadow-sm);
  border: 2px solid transparent;
  transition: all var(--transition-base);
  cursor: pointer;
  flex-shrink: 0;
}

.node.locked {
  background: var(--neutral-100);
  border: 2px solid var(--neutral-200);
  color: var(--neutral-500);
  box-shadow: none;
  cursor: not-allowed
