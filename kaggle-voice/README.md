# Kaggle Free GPU + Voice Cloning

This is where the narration voices come from. Every voice on this channel
was made on Kaggle's free GPU — no card, no trial, no bill — with the
Qwen3-TTS voice clone. The GPU lives in your signed-in Kaggle session;
Muse drives the notebook in the browser while you're signed in, and brings
the finished voice back.

## The free GPU

- **Kaggle is free — $0, no credit card, no trial.** Sign up at kaggle.com.
- **Phone verification is required** (Settings → verify phone). Skip it and
  the GPU and internet stay locked/greyed out.
- The free GPU is **GPU T4 x2**: two NVIDIA Tesla T4s, ~16 GB each.
  (The P100 was retired — do not pick it.)
- **~30 free GPU hours a week**, resets weekly. One hour on T4 x2 burns
  one quota hour. Sessions run up to 12 hours, with a ~20 minute idle
  timeout — stop the session when you're done so the quota doesn't burn.
- In a notebook: right-hand Settings pane → **Accelerator → GPU T4 x2**,
  and **Internet → On** (off by default — installs fail without it).
  The session restarts when you change the accelerator.
- Confirm it with `torch.cuda.is_available()` → `True`, 2 devices.
- Use **Save & Run All** for background runs so the work keeps going
  while you do something else.

## The voice workflow

Qwen's official flow is **VoiceDesign, then Clone**:

1. **Design a voice** (or record one): a short sample clip, 8–15 seconds
   of clean speech, plus its exact transcript.
2. **Build the clone prompt once** — `create_voice_clone_prompt` with the
   reference audio + reference text. Reuse that prompt for every script.
3. **Generate the script in chunks** — `generate_voice_qwen3.py` splits
   the narration into sentence chunks and generates each one with the
   clone prompt, then joins them into `voice.wav` (24 kHz mono).

```bash
pip install -q qwen-tts soundfile
python generate_voice_qwen3.py <video_dir>
```

`generate_voice_qwen3.py` reads `<video_dir>/script.txt` and writes
`<video_dir>/voice.wav`. Point `REF_AUDIO` at your reference clip and put
its exact transcript in `REF_TEXT` — the transcript has to match the audio
word for word, it's part of the clone prompt.

Model: `Qwen/Qwen3-TTS-12Hz-1.7B-Base` (Apache 2.0, commercial use OK).

## Included voice: Jolly

- `jolly_voice_b_bouncy.wav` (10.0s) — the reference clip for Jolly, the
  channel's narrator. `generate_voice_qwen3.py` uses it by default, with
  its exact transcript as `REF_TEXT`.
- `jolly_b_clone_test.wav` (10.3s) — a demo of the clone speaking the same
  hook back, so you can hear what the clone sounds like before running it.
- To clone a different voice, swap in your own 8–15 second clean clip and
  its exact transcript in `REF_AUDIO` / `REF_TEXT`.

## Script rules that keep the clone sounding right

These are learned the hard way — a clone is picky about its input text:

- **Write the narration in natural, conversational English.** Short,
  chopped sentences sound like a robot. Contractions, flowing sentences,
  normal connectors.
- **Numbers as words, no digits** — "fifteen minute chunks", not "15-minute".
- **No ALL-CAPS respellings.** Some clones letter-spell them ("DIE-mun"
  comes out as "D. I. Mune"). Use lowercase respellings for tricky names
  ("dye-mun") or plain spellings.
- **Tool and brand names need phonetic respellings in the voice text
  only** (never in the captions): `yt-dlp` → "why tee dee ell pee",
  `ffmpeg` → "eff em peg". The display script keeps the real names.
- **One quirk to know:** a clone can drop a consonant before certain
  sounds — ours drops the /v/ in "drive folder" (heard as "dry folder").
  Don't fight it with respellings; rephrase so the sound lands before a
  different consonant ("a folder on drive called…").
- **Short sentences, one clause each** — the generator works sentence by
  sentence, and long sentences drift.
- **Verify every voice** by re-transcribing it (faster-whisper) and
  diffing against the script. A single bad line gets re-generated as a
  fix clip and spliced in — never re-roll the whole voice for one slip.

## Pacing (after generation, before captions)

1. Join the sentence chunks with **0.35 seconds of silence** between
   sentences — a small, subtle, normal-speech pause.
2. Slow the finished voice with ffmpeg `atempo=0.945` (pitch-preserving),
   about 146 words a minute. This is the pace that sounds natural for
   narration; the raw clone runs fast.
3. **Generate captions from the slowed voice**, so the timestamps match
   the final audio. faster-whisper works; if the GPU run fails with a
   libcublas error, fall back to CPU.

## Files in this folder

| File | What it does |
|---|---|
| `generate_voice_qwen3.py` | Clone a reference voice, generate a full narration |
| `jolly_voice_b_bouncy.wav` | Reference clip for Jolly, the channel's narrator (10s) |
| `jolly_b_clone_test.wav` | Demo of the clone speaking the hook back (10s) |
| `README.md` | This file — free GPU setup + voice workflow |
