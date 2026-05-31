# 📖 Chavruta — Torah Learning Web App

A modern, self-contained Hebrew Torah/Talmud learning tool built for yeshiva classrooms and chavruta study. No backend, no build step — just open a browser.

**Live demo:** serve locally with `python3 -m http.server 8080` and open `http://localhost:8080`

---

## ✨ Features

### Mode 1 — Gemara Visualizer (ניתוח גמרא)
- Fetches any Talmud page live from the **Sefaria API**
- **Smart pre-splitting**: each Sefaria segment is broken at discourse markers (`תא שמע`, `אמר רב`, `תניא`, `:` etc.) before analysis — so a single long paragraph becomes multiple individually-tagged units
- **18 discourse types** auto-detected via Aramaic/Hebrew pattern matching:
  `קושיא · תירוץ · שאלה · תשובה · דעה · משנה · ברייתא · מעשה · הלכה · תיקו · מחלוקת · קל וחומר · דחייה · מסקנה · אגדה · פסוק · הוה אמינא · כללי`
- Displayed as **color-coded puzzle blocks** (Scratch-style notch connectors) grouped into סוגיות with auto-generated Hebrew titles
- **Mermaid v10 flowchart** — subgraph per sugya, classDef per type, safe shape set
- Manual type override dropdown per block
- Hover tooltip shows type name (Hebrew + English)
- PDF export via html2canvas + jsPDF

### Mode 2 — Chavruta (חברותא)
- Setup: enter two learner names + study topic
- **Voice calibration wizard**: each speaker talks for 4 seconds; the app learns their voice profile using `AudioContext` pitch autocorrelation + spectral centroid + zero-crossing rate
- **Auto speaker identification** — no manual toggling; the app knows who's talking
- Live **chat history** with color-coded speech bubbles (blue right / white left) + timestamps
- **Semantic flowchart**: nodes show `[Name · TypeIcon TypeName — key words]` — a meaningful summary, not a raw transcript
- Flowchart updates with 100ms debounce after each finalized utterance
- PDF export of the full conversation map

### Mode 3 — Lecture / Shiur (שיעור)
- Setup: enter rabbi name + topic → **start immediately, no calibration**
- Everything attributed to the rabbi (rabbi speaks ~95% of a shiur)
- **Zero-buffer live flowchart**: updates the instant each phrase is recognized — no setTimeout delay
- **Plain lecture-chart style**: blue rectangles, linear top-to-bottom flow, first 6 content words per node (not Gemara-style analysis)
- "Last said" live indicator shows the current phrase as it's being spoken

---

## 🏗 Architecture

| Concern | Solution |
|---|---|
| Hosting | None — pure static HTML |
| Fonts | Google Fonts (Heebo + Frank Ruhl Libre) |
| Flowcharts | Mermaid v10 (CDN) |
| PDF export | html2canvas + jsPDF (CDN) |
| Speech recognition | Web Speech API (`he-IL`, continuous) |
| Voice ID | Custom `SpeakerDetector` class (getUserMedia + AudioContext) |
| Gemara text | Sefaria REST API (no key required) |
| State | In-memory only (resets on refresh) |

---

## 🚀 Running Locally

```bash
git clone https://github.com/YOUR_USERNAME/chavrita.git
cd chavrita
python3 -m http.server 8080
```

Then open **http://localhost:8080** in Chrome.

> **Why a server?** The microphone (`getUserMedia`) and Sefaria API (CORS) require a proper origin — `file://` won't work.

---

## 🖥 Browser Requirements

| Feature | Requirement |
|---|---|
| Speech recognition | Chrome (desktop) — Web Speech API is Chrome-only on desktop |
| Microphone | Any browser that supports `getUserMedia` |
| Flowcharts | Any modern browser |

---

## 📁 File Structure

```
chavrita/
└── index.html       ← The entire app (HTML + CSS + JS, ~2000 lines)
```

Everything is intentionally in a single file for maximum portability — no npm, no bundler, no dependencies to install.

---

## 🎨 Design System

- **Language**: Hebrew throughout, RTL layout
- **Fonts**: Heebo (UI) · Frank Ruhl Libre (Torah text)
- **Brand gradient**: `#0a84ff → #5e5ce6 → #bf5af2` (blue → indigo → magenta)
- **Style**: Apple/iOS-inspired — frosted glass nav, squircle cards, spring-animated sliding pill tab indicator
- **Logo**: Gradient squircle with a white open-book icon and a circular "bite" cut out of the book

---

## 🔧 Key Technical Details

### Voice Identification (`SpeakerDetector`)
```
getUserMedia → AudioContext → AnalyserNode
  ↓
Per-frame features: pitch (autocorrelation) + spectral centroid + ZCR
  ↓
calibrate(id, 4000ms) → builds feature centroid per speaker
identify() → returns ID of nearest calibrated centroid
```

### Nikud Stripping
All pattern matching runs on nikud-stripped text:
```js
text.replace(/[֑-ׇ׳״]/g, '')
```
Sefaria returns fully vocalized Hebrew; patterns are written without nikud.

### Gemara Pre-Splitting
Before tagging, each Sefaria segment is split at:
1. `: ` (Hebrew sof-pasuk / sentence end)
2. Discourse openers: `תא שמע`, `ורמינהו`, `אמר רב`, `תניא`, `שמע מינה`, `לא קשיא`, `אלא`, `מאי קאמר`, `איתמר`, and 15+ more

This ensures each logical unit gets its own tag — a single paragraph often contains 3–5 distinct discourse moves.

### Flowchart Node Labels (Modes 2 & 3)
Nodes show semantic summaries, not raw transcript text:
```
[Speaker · TypeIcon TypeName — first 4-6 content words]
```
Common discourse openers (`אמר`, `תניא`, `הנה`, `כלומר`…) are stripped before extracting the content snippet.

---

## 📋 Tractates Supported (Mode 1)

Berakhot · Shabbat · Eruvin · Pesachim · Yoma · Sukkah · Beitzah · Rosh Hashanah · Taanit · Megillah · Moed Katan · Chagigah · Yevamot · Ketubot · Nedarim · Nazir · Sotah · Gittin · Kiddushin · Bava Kamma · Bava Metzia · Bava Batra · Sanhedrin · Makkot · Shevuot · Avodah Zarah · Horayot · Zevachim · Menachot · Chullin · Niddah

---

## 🛣 Roadmap / Ideas

- [ ] localStorage session save/load (currently resets on refresh)
- [ ] Yerushalmi support via Sefaria API
- [ ] LLM-powered sugya title generation (currently heuristic)
- [ ] Chavruta: session timer + per-exchange notes
- [ ] Lecture: auto-generated text summary after recording
- [ ] Print-friendly view
- [ ] Mobile layout improvements

---

## 📜 License

MIT — free to use, modify, and share for Torah learning purposes.
