# Kai Cenat GTA 6 Clipper — Cursor Agent Package

Clip Kai Cenat's GTA 6 Twitch stream into vertical short-form clips.
Same pipeline Muse uses for IShowSpeed — adapted for Kai.

The scripts live in the repo root — run everything from there (`adscan.py`, `transcribe.py`, `vertical.py`); this folder is just the instructions.

**Separation of duties:** Muse clips Speed. These Cursor agents clip **Kai only**.
Never mix the two channels, their recordings, or their Drive folders.

## What you need

- `ffmpeg` (8.x works; fast-seek `-ss` before `-i` can fail on these files — see Gotchas)
- `yt-dlp` (latest)
- Python 3.10+ with a venv
- A Google account for Drive uploads (see Step 8 — each agent uses its own)
- No Twitch login needed anywhere in this pipeline. Recording is anonymous.

Setup:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` is `faster-whisper`, `av>=19.0.2`, `numpy`.
Note: `transcribe.py` already contains the monkey-patch for PyAV 19
(faster-whisper passes a `metadata_errors` kwarg that PyAV 19 rejects).
If `pip install -U av` is needed, do that first.

## Step 1 — Record the stream (15-min chained parts)

```bash
timeout 900 yt-dlp -f "best[height<=1080]" --no-part --restrict-filenames \
  -o "kai-live-20261118-part1.%(ext)s" https://www.twitch.tv/kaicenat
```

- When it ends, start the next part immediately (`part2`, `part3`, ...) so there
  are no coverage gaps. Kai runs long marathon-style streams — keep the chain
  going while he is live.
- Check he is actually live before starting (open twitch.tv/kaicenat).
  If yt-dlp exits in seconds instead of 15 minutes, he is offline.
- Each part is ~700MB. Disk fills fast — see Step 9.

## Step 2 — Scan each part for moments

Ad breaks first (Twitch inserts them into every capture — never cut blind):

```bash
.venv/bin/python adscan.py kai-live-20261118-part1.mp4
```

- One line per 5s: grayscale stddev. Ad-break gradient frames score ~30 or
  below; gameplay scores ~40–70. A long run of low values = an ad break, dead.
- Quirk: on these Twitch files the displayed timestamps run ~1.77x fast
  (fps reads wrong). A displayed `400s` is really ~225s into the file.
  Use the transcript timestamps (Step 3) for cutting, not the adscan clock.

Then transcribe the whole part:

```bash
.venv/bin/python transcribe.py kai-live-20261118-part1.mp4 kai-part1-transcript.json
```

- faster-whisper `tiny`, CPU int8, word timestamps, VAD on.
- Output: JSON list of `{"start", "end", "text"}` chunks, ≤6 words / ~2.5s,
  uppercased. `example-captions.json` shows the format.
- Takes several minutes per 15-min part on CPU. One part at a time —
  do not run two transcribes at once, it slows everything to a crawl.

## Step 3 — Pick moments from the transcript

Read the transcript JSON. Pick **gameplay / reactions / chaos only**:

- First reactions, physics/chaos, funny fails, funny NPCs, discoveries,
  police chases. Best performers in that order.
- **Never clip:** story cutscenes, plot reveals, endings, isolated cutscene
  dialogue. No spoilers in the clip, the title, or the thumbnail.
- **Never clip an ad break.** Long silent gaps in the transcript (100s+ with
  no captions) are usually ad breaks — verify with a frame before cutting
  near one.
- Length: 15–45s, sweet spot 20–40s. Hook (the funny line / moment) in the
  first 1–2 seconds. End right after the payoff.

## Step 4 — Cut the moment (RE-ENCODE, never stream-copy)

```bash
ffmpeg -ss <near> -i kai-live-20261118-part1.mp4 -ss <offset> -t <dur> \
  -c:v libx264 -preset veryfast -crf 18 -c:a aac kai-moment1-raw.mp4
```

- `<near>` = a few seconds before the moment start (fast seek),
  `<offset>` = the remaining seconds to the exact start (accurate seek).
- **Do NOT use `-c copy`.** Stream-copy cuts from these Twitch recordings
  come out truncated/corrupt (a 16s cut rendered as 9s). Re-encode every cut.

## Step 5 — Captions for the cut

Either transcribe the cut file directly:

```bash
.venv/bin/python transcribe.py kai-moment1-raw.mp4 kai-moment1-captions.json
```

...or slice the matching chunks out of the full-part transcript and re-time
them to the cut (subtract the cut start from every timestamp).

- The tiny model garbles fast speech sometimes. **Hand-fix captions from the
  full transcript** when a line is wrong — the burned-in caption is what
  viewers read.
- Long merged chunks (a single caption spanning 20s+) happen when the
  transcript merges a quiet stretch. Split those by hand if they cover a
  whole beat of the clip.

## Step 6 — Render vertical

```bash
python3 vertical.py kai-moment1-raw.mp4 kai-moment1-captions.json \
  "KAI LOSES IT OVER AN NPC" kai-moment1-vertical.mp4
```

Output: 1080x1920 MP4, H.264 + AAC, `crf 20`, faststart.

- **Locked style:** blurred-background fill (full frame kept, facecam
  visible), captions **BELOW the video** in the bottom blurred area
  (ASS alignment 2, MarginV 300), never over the gameplay. Hook title card
  on top for the first 3 seconds.
- `vertical.py` writes an `.ass` file next to the output — keep it, it is
  the caption source if you need a re-render.

## Step 7 — Frame-check before uploading

```bash
ffmpeg -y -v error -i kai-moment1-vertical.mp4 -ss <mid-clip> -frames:v 1 check.png
```

Open `check.png` and confirm: real gameplay (not an ad screen, menu, or
cutscene), captions sitting below the video, hook gone after 3s.
Do not upload an unchecked clip.

## Step 8 — Upload to Drive

- Create a Google Drive folder called **`kai`** (the Speed clips live in a
  separate folder called `speed` — do not mix them). Note its folder ID.
- Upload finished `*-vertical.mp4` files there. **Never send finished clips
  in chat** — Drive is the delivery point.
- `hatch_gws_cli` is Muse-only and will not work here. Upload with whatever
  the agent's own Google account supports: `rclone`, Drive for Desktop, or
  the Google Drive API. Use the agent's own Google account, not a shared one.
- Name clips `moment<N>-vertical.mp4`, numbered in order. **Never re-upload
  a new version under an old filename** — always use a fresh versioned name
  (e.g. `moment1-vertical-v2.mp4`), or apps will play the cached old file.

## Step 9 — Delete the raw recordings

Once a part's clips are cut, verified, and uploaded, **trash the big raw
part file** (recoverable trash, not `rm`). ~700MB per part — disk fills up
in a day otherwise. Keep the small finished clips and caption JSONs.

## Accounts — the short version

- **Recording / cutting / rendering: no account at all.** yt-dlp reads the
  public stream anonymously.
- **Drive upload: one Google account per agent.** Do not share one account
  across agents.
- **Posting (TikTok / Shorts / Reels / X): one posting account per agent.**
  Do not post the same clip from two accounts, and do not submit the same
  clip to two paid campaigns (recut it with a new hook first if you must).
- Nobody posts as the channel owner. The owner posts from their own accounts.

## Rules that do not bend

- Kai only. No Speed, no other streamer, no official GTA 6 stream.
- Non-commercial fan use (Rockstar / Take-Two policy): no spoilers, no
  plot reveals, no paid raw gameplay, no promoting a product in the clip.
- No pre-release or leaked footage, no cheating / glitch / mod promotion.
- Licensed in-game radio music is a Content ID / mute risk — keep it in
  mind, do not strip audio, just do not build clips around the music.
- **The Expedia x IShowSpeed campaign does NOT apply to Kai clips.**
  It only accepted clips from Speed's Nov 6 stream. Never submit Kai clips
  there. Re-check any campaign's rules the day you submit — budgets and
  eligibility change fast.

## Files in this package

| File | What it does |
|---|---|
| `adscan.py` | Per-5s grayscale stddev scan — finds Twitch ad breaks |
| `transcribe.py` | faster-whisper tiny → timestamped caption JSON |
| `vertical.py` | ffmpeg 1080x1920 render, captions below, hook on top |
| `example-captions.json` | Caption JSON format (from a Speed clip — format only) |
| `requirements.txt` | Python deps |
