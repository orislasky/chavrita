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
- **Cross-page aware**: if a daf opens in the *middle* of a sugya (a connective like `אלא`/`והא`/`לא קשיא`), the app automatically pulls the tail of the previous amud from Sefaria so the discussion starts where it really begins
- Displayed as **color-coded puzzle blocks** (Scratch-style notch connectors) grouped into סוגיות with auto-generated Hebrew titles
- **Mermaid v10 flowchart** — subgraph per sugya, classDef per type, safe shape set
- **Hover any flowchart node** to see the full original segment text + its discourse type (Hebrew + English)
- Manual type override dropdown per block
- PDF export via html2canvas + jsPDF

### Mode 2 — Chavruta (חברותא)
- Setup: enter two learner names + study topic
- **Voice calibration wizard**: each speaker talks for 4 seconds; the app learns their voice profile using `AudioContext` pitch autocorrelation + spectral centroid + zero-crossing rate
- **Auto speaker identification** — no manual toggling; the app knows who's talking
- Live **chat history** with color-coded speech bubbles (blue right / white left) + timestamps
- **Auto speaker detection** by majority vote: the audio analyser is sampled ~11×/sec and each utterance is attributed to whoever was talking most during it (robust to Aramaic too)
- **Zero-buffer flow map**: each utterance is appended as a DOM card immediately (blue = learner A on the right, green = learner B on the left), with a live ghost node for the current phrase
- PDF export of the full conversation map

### Mode 3 — Lecture / Shiur (שיעור)
- Setup: enter rabbi name + topic → **start immediately, no voice setup**
- Stripped-down UI by design: **just a live mic indicator + the chart** — no chat, no text boxes, no speaker toggles
- Everything attributed to the rabbi (he speaks ~95% of a shiur, freely mixing Hebrew and Aramaic)
- **Local Whisper transcription**: a small Python backend (`server.py`) runs OpenAI Whisper locally via `faster-whisper`, so Hebrew **and the Aramaic** a rabbi mixes in are transcribed by a real model — far better than the browser's Web Speech API, and audio never leaves the machine
- **Near-real-time flow**: the mic is recorded in short windows, each transcribed locally and appended to the live DOM chart the instant it returns; a "listening" ghost node sits at the bottom
- **Plain lecture-chart style**: clean cards in a linear top-to-bottom flow (not Gemara-style analysis)

---

## 🏗 Architecture

| Concern | Solution |
|---|---|
| Hosting | None — pure static HTML |
| Fonts | Google Fonts (Heebo + Frank Ruhl Libre) |
| Flowcharts | Mermaid v10 for Mode 1 (static); incremental DOM cards for the live modes (zero-buffer) |
| PDF export | html2canvas + jsPDF (CDN) |
| Speech recognition (Modes 1–2) | Web Speech API (`he-IL`, continuous) |
| Speech recognition (Mode 3) | **Local Whisper** via `server.py` + `faster-whisper` (Hebrew + Aramaic) |
| Voice ID | Custom `SpeakerDetector` class (getUserMedia + AudioContext) |
| Gemara text | Sefaria REST API (no key required) |
| State | In-memory only (resets on refresh) |

---

## 🚀 Running Locally

### Quick start (Modes 1 & 2 only)
```bash
git clone https://github.com/YOUR_USERNAME/chavrita.git
cd chavrita
python3 -m http.server 8097
```
Then open **http://localhost:8097** in Chrome.

### Full setup with local Whisper (needed for Mode 3 — Shiur)
The lecture mode transcribes Hebrew + Aramaic with a **local Whisper model**, so
you run the bundled Python backend (which also serves the app):

```bash
cd chavrita
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python server.py
```
Then open **http://localhost:8097**. The model downloads once (cached in
`~/.cache/huggingface`) and then runs fully offline.

Pick accuracy vs. speed with `WHISPER_MODEL`:
```bash
WHISPER_MODEL=small    ./.venv/bin/python server.py   # fastest
WHISPER_MODEL=medium   ./.venv/bin/python server.py   # default, balanced
WHISPER_MODEL=large-v3 ./.venv/bin/python server.py   # best, slower on CPU
```

> **Why a server?** The microphone (`getUserMedia`), Sefaria API (CORS), and the
> local `/transcribe` endpoint all require a proper origin — `file://` won't work.

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
