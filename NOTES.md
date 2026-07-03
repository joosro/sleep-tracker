# Sleep Tracker — Project Notes

Personal sleep tracking web app. Two goals: practical daily sleep monitoring,
and learning software development along the way.

## Architecture

| Piece      | Choice                          |
|------------|----------------------------------|
| Backend    | Flask (Python)                  |
| Database   | Supabase (free-tier Postgres)   |
| Charts     | Plotly                          |
| Data       | Pandas                          |
| Hosting    | Render (free tier) + GitHub     |

Render chosen over Railway to start free; migration later is low-effort since
data lives independently in Supabase.

## Tracked Metrics

- **TTB** – time to bed (assumed PM; negative sign = AM, e.g. `-120` = 1:20 AM)
- **SL** – sleep latency (minutes)
- **NOA** – number of awakenings
- **WASO** – wakefulness after sleep onset (minutes)
- **EMA** – early morning awakening (minutes)
- **TOB** – time out of bed (assumed AM; negative sign = PM, e.g. `-100` = 1:00 PM)
- `1200` = midnight for TTB, noon for TOB
- Records are dated by the **TOB (wake) date**; TIB calc must account for TTB
  falling on the prior calendar day
- Optional free-text `notes` field (from source data's "Drink/caffeine" row)

## Status

### ✅ Done
- Historical import: ~75 weeks from iPhone Notes → Shortcut → iCloud for
  Windows → Python parser → 524 records upserted to Supabase `sleep_log` table
  - Handled 2 vs 4-digit years, variable days/week, malformed titles, two note
    formats (single-line concatenated + multiline)
- Supabase table: `id`, `date` (UNIQUE), `ttb`, `sl`, `noa`, `waso`, `ema`,
  `tob`, `notes`, `created_at`. RLS disabled (single-user, API key access
  control only)
- Flask app (`app.py`), credentials via `.env` / `python-dotenv`, `.gitignore`
  protecting secrets
- `requirements.txt`
- Data entry form (`/`)
- History page (`/history`) — last 30 entries, edit + delete
- Edit form (`/edit/<date>`) — date field locked (upsert key)
- Delete route (`/delete/<date>`)
- `base.html` template, nav: Log Entry / History / Dashboard
- Local dev running with `debug=True`, `host="0.0.0.0"` (iPhone access over
  local network)

### ✅ Also done
- Computed metrics: `sleep_metrics.py` module (TIB/TST/SE), computed
  on-the-fly in the `/history` route rather than stored in Supabase
- `history.html` and `edit.html` templates built (both were missing)
- Fixed `upsert()` conflict bug — `on_conflict="date"` needed since `date`
  is unique but not the primary key (`id` is); without it, edits silently
  tried to INSERT and collided with the unique constraint
- Edit/Delete rendered as matching buttons in the History table

### ✅ Also done (Dashboard)
- `/dashboard` route: pulls full history (not capped at 30), computes
  TIB/TST/SE/TTA per record via `sleep_metrics.py`, aggregates into
  Monday–Sunday weekly averages with pandas
- `dashboard.html`: four always-visible charts (Plotly.js via CDN, no new
  backend dependency) — SE%, NOA, TST vs TIB, and wakefulness metrics
  (SL/WASO/EMA/TTA) — each with a zoomable range slider, headline charts
  default to last 13 weeks
- Chart titles moved from Plotly's SVG title (doesn't wrap, clips on
  narrow screens) to plain HTML `<h2>`/`<p>` above each chart
- Verified working on both PC and phone (same Wi-Fi, PC's local IP,
  `host="0.0.0.0"` already supports this)

### 🔲 Remaining
1. **Deployment** — Render + GitHub pipeline

## Key Decisions & Learnings

- Squarespace can't run Python server processes — ruled out early
- Render and Railway are interchangeable here since data is decoupled in
  Supabase; switching later is cheap
- Date-as-unique-key + upsert = dedup strategy
- TTB/TOB cross-midnight math is the trickiest edge case — isolate and test
  it (e.g. in a scratch notebook) before wiring into `app.py`
- Supabase free-tier projects auto-pause after ~1 week idle — restore from
  the dashboard ("Restore project") if this happens again

## Folder Structure

```
sleep-tracker/
├── app.py
├── requirements.txt
├── .env                 (not committed)
├── .gitignore
├── NOTES.md              (this file)
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── history.html
│   └── edit.html
├── static/                (CSS, if any)
└── scripts/                (one-off import scripts, prototyping notebooks)
```

## Working Style

- Building in chat with Claude, not Claude Code/Cowork, since learning the
  code itself is part of the goal — every file and command gets explained.
- Prototype tricky logic (e.g. TIB midnight math) in a scratch
  notebook/script under `scripts/` before graduating it into `app.py`.
- Update this file as phases complete or decisions change.

## Log

- **2026-07-03**: Resumed project after a break. Supabase project had
  auto-paused from inactivity; restored via dashboard. Set up formal folder
  structure and this notes file. Next: computed metrics (TIB/TST/SE).
- **2026-07-03 (cont.)**: Moved a plaintext credentials file
  (`Sleep Tracker keys.txt`) out of the repo after realizing it wasn't
  protected by `.gitignore` — values already lived in `.env`, so the file
  was safely deleted. Built `sleep_metrics.py` (TIB/TST/SE, handles
  midnight-crossing TTB/TOB), verified against real historical data.
  Discovered `history.html` and `edit.html` were never actually saved
  (only `base.html`/`entry.html` existed) — built both. Fixed a Supabase
  `upsert()` bug where edits failed with a duplicate-key error because
  `date` is unique but not the primary key; fixed with `on_conflict="date"`.
  History page now fully functional: view, edit, delete, with live
  TIB/TST/SE columns. Next: Dashboard (Plotly weekly trend charts).
- **2026-07-03 (cont.)**: Built `/dashboard` with pandas weekly aggregation
  and four Plotly.js charts (SE%, NOA, TST/TIB, wakefulness metrics), all
  with zoomable range sliders. Fixed a chart-title text-clipping bug by
  switching to HTML headings instead of Plotly's native title. Verified on
  desktop and iPhone over local Wi-Fi. Computed metrics and dashboard
  phases both complete. Next: deployment (Render + GitHub).
