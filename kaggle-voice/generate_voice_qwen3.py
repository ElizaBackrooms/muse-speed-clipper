"""Narration voice with Qwen3-TTS, cloning a reference voice.

Official Qwen workflow: VoiceDesign then Clone — a short sample clip of the
voice you want is fed to the 1.7B Base model as a reference, a reusable
voice-clone prompt is built once, then the full script is generated in
chunks with that prompt.

Run on a Kaggle free GPU (GPU T4 x2 — see README.md in this folder).
Usage:
  python generate_voice_qwen3.py <video_dir>
Reads <video_dir>/script.txt (strips a "SOURCES NOTE" footer if present)
and writes <video_dir>/voice.wav.
Install first: pip install -q qwen-tts soundfile
Model: Qwen/Qwen3-TTS-12Hz-1.7B-Base (Apache 2.0, commercial use OK).
"""
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

# The included reference voice is Jolly (Take B, "Bouncy") — the voice of
# the channel's Muse series. Swap in your own clip + transcript to clone
# a different voice; the transcript must match the audio word for word,
# it's part of the clone prompt.
REF_AUDIO = "jolly_voice_b_bouncy.wav"
REF_TEXT = (
    "Muse got locked out of America's biggest bank, sold a man's stuff to "
    "a stranger, and planned an eight thousand dollar Christmas. This is "
    "what people built with Muse today. Five stories."
)


def split_script(script: str):
    parts = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    chunks = []
    for p in parts:
        if len(p) <= 600:
            chunks.append(p)
        else:
            chunks.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip())
    return chunks


if __name__ == "__main__":
    from qwen_tts import Qwen3TTSModel

    video_dir = Path(sys.argv[1])
    here = Path(__file__).resolve().parent

    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        device_map="cuda:0", dtype=torch.bfloat16)
    prompt = model.create_voice_clone_prompt(
        ref_audio=str(here / REF_AUDIO), ref_text=REF_TEXT,
        x_vector_only_mode=False)
    script = (video_dir / "script.txt").read_text()
    # Strip the SOURCES NOTE at the end (not narration) if present.
    script = script.split("---\nSOURCES NOTE")[0].strip()
    audio_parts, sr = [], None
    for chunk in split_script(script):
        wavs, sr = model.generate_voice_clone(
            text=chunk, language="English", voice_clone_prompt=prompt)
        audio_parts.append(np.asarray(wavs[0], dtype=np.float32))
        print(f"Generated chunk ({len(chunk)} chars)")
    out = video_dir / "voice.wav"
    sf.write(str(out), np.concatenate(audio_parts), sr)
    print(f"Wrote {out} ({sum(len(a) for a in audio_parts) / sr:.1f}s)")
