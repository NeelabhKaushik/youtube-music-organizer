# YouTube Music mood organizer

A lightweight, one-time Python workflow for organizing Liked Songs into seven
private mood playlists. No paid AI APIs, audio downloads, web app or database.
It only creates new playlists and adds songs to playlists it owns. It never
removes likes or modifies unrelated playlists.

## Setup (macOS / Linux, Python 3.10+)

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Authenticate locally

1. Open music.youtube.com while logged in. Open browser Developer Tools → Network.
2. Filter for `browse`, then click Library. Select a successful POST request.
3. Copy the complete **request headers** using the browser's copy headers action.
   Chrome may require the raw headers view. Do not copy response headers or a whole
   JavaScript fetch command. See the official instructions below for browser details.
4. From this project folder on macOS, run:

```sh
pbpaste | .venv/bin/python auth_setup.py
```

Headers go directly from your clipboard into ignored `secrets/browser.json` with
owner-only permissions. Never paste them into a chat, issue, commit or command
argument. Clear your clipboard afterward. For other systems, pipe a protected
local headers file into the same script and remove that temporary file yourself.

Official guide: https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html

## Export and classify (no account changes)

```sh
.venv/bin/python organizer.py export
.venv/bin/python organizer.py batches --size 40
```

`get_liked_songs(limit=None)` delegates full pagination to ytmusicapi. The raw
response and CSV of every returned track are preserved in timestamped backups.
Full metadata is retained, including missing-ID entries. `library.json` contains
unique actionable video IDs. The reported total is compared with fetched entries;
unverified exports require explicit acknowledgement before upload. Compare the
exported total with the account, especially if unavailable tracks are present.
A failed export does not replace the previous snapshot. Keep the library stable
while exporting: the upstream API cannot provide an atomic snapshot.

Open `data/batches/<run>/instructions.txt` and the batches in this Codex chat.
Ask Codex to classify each batch and save its JSON array locally, then import it:

```sh
.venv/bin/python organizer.py import data/results/001.json
.venv/bin/python organizer.py preview
```

This uses the current conversation's included usage, not an API key. No Python
model endpoint is called. Stop and wait if included usage is exhausted; never buy
credits or switch to paid APIs. An optional local Ollama model can produce the
same JSON format, but model selection/download is deliberately not automatic.
There is no trained classifier bundled with this project.

Song-specific knowledge and verified public sources can inform classification.
Use free YouTube metadata already exported; optionally research unfamiliar songs
using public artist/label pages or MusicBrainz, recording URLs in `evidence`.
No automatic scraping or unverified lyrics/tempo estimates. Audio analysis is not
implemented because the library does not grant downloadable audio access; only
consider it if authorized local audio is supplied.

Categories: Jolly / Feel Good, High Adrenaline, Sad / 2 AM, Deep Focus,
Chill / Late Night, Romantic, DHH Essentials. Multiple assignments are allowed.
DHH and mood are separate decisions. Unknown songs are flagged, not guessed.

Result example (replace with an actual exported ID):

```json
[{
  "videoId": "actual-video-id",
  "categories": [],
  "confidence": 0.2,
  "explanation": "Song version is unfamiliar; listening review needed.",
  "needs_review": true,
  "evidence": ["Supplied title and artist only"]
}]
```

Results are cached by video ID; new batch runs skip cached tracks. If metadata or
song-version interpretation changes, reclassify and import that ID explicitly.
Imports validate the whole file before saving. Review by editing result JSON and
reimporting it; CSV is for inspection, not import. A confidence below 0.75, empty
categories or `needs_review=true` excludes a track from uploads. Confidence is a
subjective review aid, not a calibrated probability.

## Inspect before approving

Read `data/preview.csv` and `data/preview.txt`. These show totals, proposed and
upload-ready category counts, overlaps, explanations, evidence, uncertain songs,
and category samples. `data/plan.json` lists exact upload IDs and excluded IDs.
All songs must have a classification record before upload, including uncertain
ones. Uncertain songs remain excluded unless reviewed and reimported.

**Do not run the next command until the user explicitly approves the preview.**

```sh
.venv/bin/python organizer.py apply --approve HASH_FROM_PREVIEW
```

Approval is bound to the exact library, classifications and playlist plan.
Changed inputs invalidate it. The command creates all seven PRIVATE playlists,
including empty ones, and uploads batches of 50. It does not send messages.
If the upstream count could not be verified, inspect the export and explicitly
add `--accept-incomplete` only after accepting that limitation.

Sync state is stored locally in `data/sync.json`; preserve it and its ownership
markers. Every rerun reads remote contents before adding missing IDs. Failed
writes are reconciled against the server; no blind replay of playlist creation.
If creation timed out, use `organizer.py recover` to find the unique ownership
marker, then rerun apply. If recovery cannot find exactly one match, it stops for
manual inspection. Never delete sync state to resolve an error: that could create
duplicate playlists. Concurrent runs against the same data directory are locked.

`data/final-report.json` contains links and verified song counts. Existing
project playlists are only appended to; subsequent changed plans do not remove
old entries. This is a one-time organizer, not a destructive mirror synchronizer.

## Tests and cleanup

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests use fake clients and temporary data; they never access your account.
Runtime packages live exclusively in `.venv`. Keep them while the workflow is
active. After completion, remove that environment if no reruns are needed.
Do not delete backups, sync state or credentials without an explicit decision.
Never remove pre-existing system packages. See AGENTS.md and MEMORY.md.

The project is an unofficial client; upstream authentication or API changes can
interrupt it. Private data and credentials are ignored by Git.
