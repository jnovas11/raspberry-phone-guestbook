from __future__ import annotations

import os
import random
import wave
from datetime import datetime
from pathlib import Path


class RecordingStore:
    def __init__(self, directory: Path, minimum_seconds: float):
        self.directory = directory
        self.minimum_seconds = minimum_seconds
        self.directory.mkdir(parents=True, exist_ok=True)
        self.last_played: Path | None = None

    def new_temporary_path(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        return self.directory / f".recording-{stamp}.part.wav"

    def commit(self, temporary_path: Path) -> Path | None:
        if self.duration(temporary_path) < self.minimum_seconds:
            temporary_path.unlink(missing_ok=True)
            return None
        final_name = temporary_path.name.removeprefix(".recording-").replace(
            ".part.wav", ".wav"
        )
        final_path = self.directory / final_name
        os.replace(temporary_path, final_path)
        return final_path

    def random_recording(self, avoid_repeat: bool = True) -> Path | None:
        candidates = [
            path
            for path in self.directory.glob("*.wav")
            if self.duration(path) >= self.minimum_seconds
        ]
        if avoid_repeat and len(candidates) > 1 and self.last_played in candidates:
            candidates.remove(self.last_played)
        if not candidates:
            return None
        selected = random.choice(candidates)
        self.last_played = selected
        return selected

    @staticmethod
    def duration(path: Path) -> float:
        try:
            with wave.open(str(path), "rb") as wav_file:
                return wav_file.getnframes() / wav_file.getframerate()
        except (OSError, EOFError, wave.Error, ZeroDivisionError):
            return 0.0

