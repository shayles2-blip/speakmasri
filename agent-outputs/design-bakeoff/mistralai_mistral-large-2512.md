Here’s a **crafted, premium evolution** of SpeakMasri’s design system while keeping green as the anchor. The goal is to elevate the execution to feel intentional, tactile, and sophisticated—without losing the app’s playful, approachable essence.

---

### **1. Refined Palette**
**Keep green as primary**, but refine it to feel richer and less neon. Add depth with supporting neutrals and accents that feel warm, modern, and premium.

| Role               | Hex       | Notes                                                                 |
|--------------------|-----------|-----------------------------------------------------------------------|
| **Primary Green**  | `#4A9E00` | Deeper, less saturated than `#58cc02` (less "cartoonish").            |
| **Green Dark**     | `#3A7D00` | For shadows/active states (replaces `#58a700`).                       |
| **Green Light**    | `#A3D977` | Subtle highlight for backgrounds (e.g., correct answers).             |
| **Accent Blue**    | `#2A82DA` | Cooler than `#1cb0f6` (more professional, less "Duolingo").           |
| **Accent Yellow**  | `#F5B800` | Warmer than `#ffc800` (feels premium, not "warning").                 |
| **Accent Red**     | `#E54D4D` | Less aggressive than `#ff4b4b` (softer feedback).                     |
| **Text**           | `#2A2A2A` | Darker than `#3c3c3c` (better contrast, more serious).                |
| **Text Secondary** | `#6B6B6B` | For subtitles/captions (replaces `#666`).                             |
| **Border**         | `#E0E0E0` | Lighter than `#e5e5e5` (softer, less "default").                      |
| **Background**     | `#F9F9F9` | Warmer than `#fff` (less sterile).                                    |
| **Surface**        | `#FFFFFF` | For cards/buttons (pure white for contrast).                          |
| **Shadow**         | `#0000001A` | 10% opacity black (softer than current hard shadows).                |

---

### **2. Typography**
**Replace Nunito** with a pairing that feels premium, legible, and culturally aligned:
- **Headlines/Buttons**: **Inter** (Google Font)
  - *Why*: Neutral, highly legible, and widely used in premium apps (e.g., Notion, Linear). Works in both LTR and RTL.
  - *Weights*: `700` (bold), `800` (extra-bold for emphasis).
- **Body/Text**: **Tajawal** (Google Font)
  - *Why*: Designed for Arabic, with a modern, clean aesthetic. Pairs well with Inter for Latin text.
  - *Weights*: `400` (regular), `500` (medium for subtitles).
- **Franco (Arabic chat)**: Keep as-is, but reduce opacity to `60%` (softer, less "sticker-like").

**Font Sizes**:
- **H1**: `28px` → `32px` (more generous).
- **H2**: `22px` → `24px`.
- **Body**: `16px` → `17px` (better readability).
- **Buttons**: `16px` → `16px` (keep uppercase, but reduce letter-spacing to `0.5px` for sophistication).

---

### **3. Component Philosophy**
#### **Buttons**
- **Shape**: Rounded corners (`12px` radius, down from `16px`) for a more modern, less "bubble-like" feel.
- **Elevation**:
  - *Rest*: Subtle shadow (`0 2px 4px #0000001A`, `0 1px 2px #0000000F`).
  - *Active*: Pressed state uses `transform: translateY(1px)` (softer than `4px`) + shadow removed.
  - *Disabled*: Replace `#e5e5e5` with `#F0F0F0` (warmer gray).
- **Motion**: Add a `0.15s` ease-out transition for all interactions (smoother than `0.08s`).

#### **Cards/Options**
- **Border**: Replace `2px solid #e5e5e5` with `1px solid #E0E0E0` (thinner, more refined).
- **Feedback States**:
  - *Correct*: `#A3D977` background (softer green) + `1px solid #4A9E00` border.
  - *Wrong*: `#FFE5E5` background (softer red) + `1px solid #E54D4D` border.
  - *Selected*: `#E8F2FF` background (softer blue) + `1px solid #2A82DA` border.
- **Shadow**: Remove hard `0 2px 0` shadows; use `0 2px 8px #0000000A` for depth.

#### **Path/Lesson List**
- **Nodes**:
  - Replace circles with **rounded squares** (`16px` radius) for a more modern, less "gamified" look.
  - *Active*: `#4A9E00` fill + `0 4px 8px #0000001A` shadow.
  - *Completed*: `#F5B800` fill + subtle inner shadow (`inset 0 1px 2px #0000001A`).
  - *Locked*: `#F0F0F0` fill + `1px solid #E0E0E0` border.
- **Layout**: Keep the winding path, but reduce node size to `60px` (from `70px`) and spacing to `16px` (from `24px`) for tighter hierarchy.

#### **Exercise Screens**
- **Progress Bar**:
  - Replace `#border` with `#E0E0E0` and `#green` with `#4A9E00`.
  - Add a subtle gradient (`linear-gradient(90deg, #4A9E00, #6BC900)`) for depth.
- **Audio Button**:
  - Replace hard shadow with `0 4px 12px #0000001A`.
  - Add a `0.2s` scale animation on press (`transform: scale(0.95)`).
- **Feedback Popups**:
  - Replace flat colors with **glassmorphism** (e.g., `#A3D977` at `80%` opacity + `backdrop-filter: blur(4px)`).
  - Rounded corners (`16px` radius).

#### **Navigation**
- **Bottom Bar**:
  - Replace `2px solid #e5e5e5` with `1px solid #E0E0E0`.
  - Active tab: `#2A82DA` underline (thicker: `3px` → `4px`).
  - Icons: Use **SF Symbols** (iOS) or **Material Icons** (Android) for consistency.

---

### **4. Concrete Implementation**
#### **CSS Updates**
```css
:root {
  /* Colors */
  --green: #4A9E00;
  --green-d: #3A7D00;
  --green-l: #A3D977;
  --blue: #2A82DA;
  --yellow: #F5B800;
  --red: #E54D4D;
  --text: #2A2A2A;
  --text-secondary: #6B6B6B;
  --border: #E0E0E0;
  --bg: #F9F9F9;
  --surface: #FFFFFF;
  --shadow: 0 2px 4px #0000001A, 0 1px 2px #0000000F;
  --radius: 12px;
}

/* Typography */
body {
  font-family: 'Tajawal', 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
}
h1, h2, .btn, .stat {
  font-family: 'Inter', sans-serif;
  font-weight: 800;
}
.ar {
  font-family: 'Tajawal', 'Cairo', sans-serif;
}

/* Buttons */
.btn {
  background: var(--green);
  color: var(--surface);
  border-radius: var(--radius);
  padding: 14px 24px;
  font-size: 16px;
  box-shadow: var(--shadow);
  transition: all 0.15s ease-out;
}
.btn:active {
  transform: translateY(1px);
  box-shadow: 0 1px 2px #0000000F;
}
.btn-blue {
  background: var(--blue);
  box-shadow: 0 2px 4px #0000001A, 0 1px 2px #0000000F;
}

/* Path */
.node {
  width: 60px;
  height: 60px;
  border-radius: 16px; /* Rounded square */
  background: var(--green);
  box-shadow: 0 4px 8px #0000001A;
}
.node.done {
  background: var(--yellow);
  box-shadow: inset 0 1px 2px #0000001A;
}

/* Feedback */
.feedback {
  background: rgba(163, 217, 119, 0.8); /* Glassmorphism */
  backdrop-filter: blur(4px);
  border-radius: 16px 16px 0 0;
}
```

#### **Key Changes Summary**
| Component       | Before                          | After                                  |
|-----------------|---------------------------------|----------------------------------------|
| **Green**       | `#58cc02` (neon)                | `#4A9E00` (richer)                     |
| **Buttons**     | Hard shadows, `16px` radius     | Soft shadows, `12px` radius            |
| **Path Nodes**  | Circles, `70px`                 | Rounded squares, `60px`                |
| **Feedback**    | Flat colors                     | Glassmorphism + blur                   |
| **Typography**  | Nunito                          | Inter (headlines) + Tajawal (body)     |
| **Shadows**     | Hard `0 4px 0`                  | Soft `0 2px 4px #0000001A`             |

---

### **Why This Works**
- **Premium Feel**: Softer shadows, refined typography, and glassmorphism elevate the design without losing the app’s playful spirit.
- **Brand Consistency**: Green remains the anchor, but the supporting palette and micro-interactions make it feel intentional.
- **Cultural Fit**: Tajawal ensures Arabic text feels native, while Inter keeps Latin text modern.
- **Accessibility**: Higher contrast (e.g., `#2A2A2A` text) and smoother transitions improve usability.
