#!/usr/bin/env python3
"""Sample one frame every 5s from a clip and print grayscale stddev.
Ad-break gradient frames score low (~<30); gameplay scores much higher."""
import math
import sys
import av
import numpy as np

path = sys.argv[1]
container = av.open(path)
stream = container.streams.video[0]
fps = float(stream.average_rate)
if math.isnan(fps) or fps <= 0:
    fps = 30.0
step = int(fps * 5)
idx = 0
for frame in container.decode(stream):
    if idx % step == 0:
        arr = frame.to_ndarray(format="gray").astype(np.float32)
        print(f"{idx / fps:6.1f}s  stddev={arr.std():6.1f}")
    idx += 1
