#!/usr/bin/env python3
"""Build a 9:16 vertical clip from a 16:9 moment with burned-in captions + hook.

Usage: vertical.py <moment_raw.mp4> <captions_json> <hook_text> <output_mp4>
- 1080x1920, blurred-background fill (full frame kept, facecam safe)
- Captions: ALL CAPS chunks from Whisper, bold white + yellow current word is
  approximated by a single bold style (karaoke word-highlight needs per-word
  ASS events; chunk style here), under the video, in the bottom blurred area.
- Hook: bold title card, top third, first 3 seconds.
"""
import json, subprocess, sys, textwrap

SRC, CAPS, HOOK, OUT = sys.argv[1:5]

with open(CAPS) as f:
    caps = json.load(f)

# --- ASS subtitle file: captions in the middle band, hook as a top title ---
def ass_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

lines = []
lines.append("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\nScaledBorderAndShadow: yes\n")
lines.append("[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    "Style: Cap,DejaVu Sans,64,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,40,40,300,1\n"
    "Style: Hook,DejaVu Sans,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,8,60,60,150,1\n")
lines.append("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
hook_wrapped = "\\N".join(textwrap.wrap(HOOK, width=22))
lines.append(f"Dialogue: 0,{ass_time(0)},{ass_time(3.0)},Hook,,0,0,0,,{hook_wrapped}\n")
for c in caps:
    text = c["text"].replace("\n", " ")
    wrapped = "\\N".join(textwrap.wrap(text, width=20))
    lines.append(f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Cap,,0,0,0,,{wrapped}\n")

ass_path = OUT + ".ass"
with open(ass_path, "w") as f:
    f.write("".join(lines))

vf = (
    "[0:v]split[a][b];"
    "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "gblur=sigma=30,eq=brightness=-0.25[bg];"
    "[b]scale=1080:-2[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2,"
    f"ass={ass_path}[v]"
)
cmd = ["ffmpeg", "-y", "-v", "error", "-i", SRC,
       "-filter_complex", vf, "-map", "[v]", "-map", "0:a",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
       "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", OUT]
print(" ".join(cmd))
r = subprocess.run(cmd)
sys.exit(r.returncode)
