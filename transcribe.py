#!/usr/bin/env python3
"""Transcribe a clip with faster-whisper (tiny, CPU) and emit caption chunks.

Usage: transcribe.py <media_file> <out_json>
Chunks: up to 6 words or ~2.5s, text uppercased for karaoke-style captions.
"""
import json, sys
# PyAV 19 removed the metadata_errors kwarg that faster-whisper passes to
# av.open; drop it so decode_audio works with the installed PyAV.
import av
_orig_open = av.open
def _open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_open(*args, **kwargs)
av.open = _open
from faster_whisper import WhisperModel

media, out = sys.argv[1], sys.argv[2]
model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, _ = model.transcribe(media, word_timestamps=True, vad_filter=True)
caps, cur, cur_start = [], [], None
for seg in segments:
    for w in seg.words:
        if cur_start is None:
            cur_start = w.start
        cur.append(w.word.strip())
        if len(cur) >= 6 or (w.end - cur_start) >= 2.5:
            caps.append({"start": round(cur_start, 2), "end": round(w.end, 2),
                         "text": " ".join(cur).upper()})
            cur, cur_start = [], None
if cur:
    caps.append({"start": round(cur_start, 2), "end": round(seg.words[-1].end, 2),
                 "text": " ".join(cur).upper()})
with open(out, "w") as f:
    json.dump(caps, f, indent=1)
print(f"{len(caps)} captions -> {out}")
for c in caps[:8]:
    print(f"  {c['start']:>6.2f}-{c['end']:>6.2f}  {c['text']}")
