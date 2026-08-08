Here’s the concrete, buildable specification for both features within a single‑file vanilla JS + localStorage app.

---

### 1. Personalization – Partner‑Added Phrases via JSON File Import

**Data model**  
Add `CUSTOM_PHRASES` array to localStorage (default `[]`). Each item has `{ en, ar, franco, source: "partner" }`. A virtual “Custom Phrases” unit containing one lesson is merged at the end of the course, populated from this array.

**UI/UX & mechanism**  
- **Export template**  
  – Main menu → “Partner Phrases” → “Download Template”.  
  – App generates and forces download of a `partner_phrases_template.json` file containing a sample entry: `[{ "en": "Auntie Mona", "ar": "خالة منى", "franco": "khalto Mona" }]`. The learner sends this file to the partner (email, chat, etc.).

- **Partner fills & returns**  
  – Partner edits the JSON with any text editor (phone/desktop), adding up to 50 real‑life phrases, then sends the file back.

- **Import**  
  – Learner returns to “Partner Phrases” → “Import Phrases”.  
  – A file picker opens (`<input type="file" accept=".json">`). On selection, the file is read with `FileReader`.  
  – Data is parsed and validated (must be an array, each object contains `en`, `ar`, `franco` strings). Invalid or duplicate `en` entries are silently skipped (warning shown if >50 items).  
  – Valid items are pushed into `CUSTOM_PHRASES` and saved. The custom unit refreshes.

- **Viewing/deletion**  
  – The custom unit displays as a standard lesson; each vocab card has a small “partner” tag and a trash icon. Tapping the icon removes the item from `CUSTOM_PHRASES`.

**Why this works** – No server needed. The partner never touches the learner’s device or localStorage; the only shared artifact is a plain text file that can be transmitted over any messaging tool.

---

### 2. Register Awareness – Teaching / Flagging Appropriate Usage

**Data model**  
Add `register` property to every vocab object: `"intimate"`, `"casual"`, `"formal"`, or `"neutral"` (default). A constant maps registers to target audiences:  
```js
REGISTER_TO_AUDIENCE = {
  intimate: "Partner/loved one",
  casual: "Close friend",
  formal: "Respected elder"
}
```

**UI warnings**  
- In vocab lists and flashcards, a small coloured icon (♥ for intimate, 🙂 for casual, 👑 for formal) appears beside the word.  
- Tapping the icon shows a tooltip: *“Use only with [partner]”*, etc. Neutral items show nothing.

**Quiz mechanic**  
During lesson practice, after every vocab item with a non‑neutral `register`, the app injects one extra “Context Check” step:  
- A modal appears with the question *“Who is this most appropriate for?”* and three buttons: “Partner/loved one”, “Close friend”, “Respected elder”.  
- The correct answer is pre‑determined from the mapping.  
- The user taps an option → immediate feedback: green ✔ with brief explanation, or red ✘ with the right answer highlighted.  
- Incorrect answers are noted; after the lesson, the summary shows register‑miss stats.

**Integration** – The practice flow (flashcards, quiz) already cycles through items; the pop‑up is added as an extra step using the same item object, requiring only one conditional check. No additional question‑type templates are needed. The feature works with any existing quiz format because it simply intercepts a vocab item after its main review.

**Benefit** – Learners don’t just see a label; they actively practice choosing the correct register for a social context, reinforcing when to use each phrase.
