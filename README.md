# Project Aegis / A.N.I.E. (Acuity Narrative Integrity Engine)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](aegis-backend)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)](aegis-backend)
[![React Native](https://img.shields.io/badge/React%20Native-Expo-61DAFB?logo=react&logoColor=white)](anie-mobile)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Manifest%20V3-4285F4?logo=googlechrome&logoColor=white)](aegis-extension-mvp)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)
[![Live site](https://img.shields.io/badge/live-goanie.com-0a9396)](https://www.goanie.com)

Open-source forensic analysis platform that detects manipulation, bias, and psychological operations ("psyops") in news articles and web content.

Given a URL or body of text, the system returns a **0–100 Narrative Integrity Score** along with a detailed breakdown across four forensic vectors: Reality Anchoring, Tribal Engineering, Neuro-Linguistic Intent, and Logical Integrity.

Live site: [www.goanie.com](https://www.goanie.com)

> If this project is useful to you, please **star the repo** — it helps others discover it.

---

## Table of Contents

- [What's in this repo](#whats-in-this-repo)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
  - [Backend](#1-backend-aegis-backend)
  - [Website](#2-website-anie-site)
  - [Chrome extension](#3-chrome-extension-aegis-extension-mvp)
  - [Mobile app](#4-mobile-app-anie-mobile)
- [Environment variables](#environment-variables)
- [API overview](#api-overview)
- [Full documentation](#full-documentation)
- [Contributing](#contributing)
- [License](#license)

---

## What's in this repo

This is a monorepo containing every client and service that powers A.N.I.E.:

| Folder | Description |
|---|---|
| [aegis-backend/](aegis-backend) | Python FastAPI service. Exposes `/v1/scan`, `/v1/chat`, `/v1/feedback`, `/v1/stats`. Runs the analysis engine, scraper, and cache. |
| [anie-site/](anie-site) | Static HTML/CSS/JS website (deployed on Netlify). |
| [aegis-extension-mvp/](aegis-extension-mvp) | Chrome Manifest V3 extension for in-page article scanning. |
| [anie-mobile/](anie-mobile) | React Native / Expo mobile app (iOS + Android) with a native share-sheet extension. |
| [DOCUMENTATION.md](DOCUMENTATION.md) | Complete technical documentation (architecture, engine internals, DB schema, Synapse directive history, API reference). |

---

## How it works

```
        Chrome Extension   Mobile App   Website
                \             |             /
                 \            |            /
                  \_________  |  _________/
                            \ | /
                             \|/
                              v
                   ┌─────────────────────┐
                   │  FastAPI Backend    │
                   │  (aegis-backend/)   │
                   └──────────┬──────────┘
                              │
          ┌───────────────────┼────────────────────┐
          v                   v                    v
      Supabase            xAI Grok            Tavily
      (cache +          (analysis             (truth
      events)            engine)              layer)
```

**Scan flow:**

1. Client (extension / mobile / website) POSTs a URL (or raw text) to `/v1/scan`.
2. Backend checks the Supabase cache (24-hour TTL, keyed by a normalized URL hash).
3. On cache miss, the scraper fetches article text (Firecrawl → Jina.ai → direct fetch).
4. The engine extracts source claims and runs parallel Tavily searches for fact-context.
5. The xAI Grok model applies the **Psyop Hunter Protocol** — a 24-marker forensic checklist across four vectors — and returns a score, verdict, per-vector flags, and an overall analysis.
6. The result is cached, logged to the `scan_events` ledger, and returned to the client.

For the full scoring algorithm (Quote Shield, Red-Line Crash, Weakest-Link Rule, etc.), see [DOCUMENTATION.md](DOCUMENTATION.md#analysis-engine).

---

## Tech stack

| Component | Technology |
|---|---|
| Backend API | Python 3 + FastAPI (deployed on Render) |
| Analysis engine | xAI `grok-4-1-fast-reasoning` (2M context) |
| Truth layer | Tavily API |
| Scraping | Firecrawl (primary), Jina.ai (fallback), Archive.today, direct fetch |
| Database / cache | Supabase (PostgreSQL) |
| Website | Static HTML/CSS/JS (Netlify) |
| Mobile | React Native + Expo |
| Extension | Chrome Manifest V3 |

---

## Quick start

Clone the repo:

```bash
git clone https://github.com/goshtasb/Anie.git
cd Anie
```

You will need API keys for xAI, Tavily, Firecrawl, and a Supabase project. See [Environment variables](#environment-variables) below.

### 1. Backend ([aegis-backend/](aegis-backend))

```bash
cd aegis-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create a .env file with the keys listed below
cp ../.env.example .env   # if you have one, otherwise create manually

uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Health check: `GET /`.

Run the internal logic tests:

```bash
python test_logic.py
```

Apply the database schema to your Supabase project using [aegis-backend/supabase_schema.sql](aegis-backend/supabase_schema.sql).

### 2. Website ([anie-site/](anie-site))

Fully static. Serve it any way you like:

```bash
cd anie-site
python3 -m http.server 8080
```

Then open `http://localhost:8080`. Before deploying, update the API base URL inside `index.html` to point at your backend.

### 3. Chrome extension ([aegis-extension-mvp/](aegis-extension-mvp))

1. Open `chrome://extensions/`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked** and select the `aegis-extension-mvp/` folder.
4. Pin the extension, open any article, and click **Scan**.

Before publishing your own build, update the backend URL in `background.js`. See [aegis-extension-mvp/README.md](aegis-extension-mvp/README.md) for architecture details.

### 4. Mobile app ([anie-mobile/](anie-mobile))

```bash
cd anie-mobile
npm install
npx expo prebuild
npx expo run:ios        # or: npx expo run:android
```

The app supports two entry points:
- **MainDashboard** — open the app and paste/enter a URL.
- **ShareModal** — share a link from Safari / Twitter / etc. via the native share sheet.

Bundle ID: `com.axiom.anie`.

---

## API overview

Base URL (production): `https://aegis-alpha.onrender.com`

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/v1/scan` | Analyze an article (URL or text) |
| `POST` | `/v1/chat` | Interrogation Mode — follow-up Q&A on a scan |
| `POST` | `/v1/feedback` | Submit 👍 / 👎 on a scan result |
| `GET` | `/v1/stats` | Aggregate stats for the live ticker |
| `DELETE` | `/v1/cache/clear` | Debug: clear the scan cache |

Full request / response schemas are in [DOCUMENTATION.md](DOCUMENTATION.md#api-reference).

---

## Full documentation

[DOCUMENTATION.md](DOCUMENTATION.md) covers:

- System architecture
- Backend module-by-module breakdown (`main.py`, `engine.py`, `services.py`, `scraper.py`)
- The 24 forensic markers across all four vectors
- Scoring algorithm, Quote Attribution Protocol, Red-Line rules
- Database schema for `scan_cache`, `scan_events`, `guests`
- Synapse directive history (V3.0 → V6.0)
- Deployment instructions for each component
- Full API reference

---

## Contributing

Contributions, issues, and feature requests are welcome.

1. Fork the repo.
2. Create a feature branch: `git checkout -b feat/your-idea`.
3. Make your changes. For backend changes, run `python test_logic.py`.
4. Commit with a clear message describing *why*, not just *what*.
5. Open a pull request against `main`.

Please do not commit secrets, `.env` files, or anything containing API keys.

For larger changes (new vectors, scoring changes, new engines), open an issue first so we can align on approach.

---

## License

Released under the [MIT License](LICENSE) — you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, as long as the original copyright notice and license are included.

---

## Contact

- Website: [www.goanie.com](https://www.goanie.com)
- Repo: [github.com/goshtasb/Anie](https://github.com/goshtasb/Anie)
