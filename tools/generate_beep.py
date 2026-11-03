from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

RATE = 16_000
DURATION = 0.35
FREQUENCY = 880
AMPLITUDE = 12_000

destination = Path(__file__).resolve().parents[1] / "sounds" / "beep.wav"
destination.parent.mkdir(parents=True, exist_ok=True)

with wave.open(str(destination), "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(RATE)
    for index in range(int(RATE * DURATION)):
        sample = int(AMPLITUDE * math.sin(2 * math.pi * FREQUENCY * index / RATE))
        wav_file.writeframesraw(struct.pack("<h", sample))

print(destination)

