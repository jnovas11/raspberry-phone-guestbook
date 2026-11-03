from __future__ import annotations

import logging
import signal
import subprocess
import time
from pathlib import Path
from typing import Callable

from .config import Config
from .events import Event

LOG = logging.getLogger(__name__)
StopCheck = Callable[[], Event]


class AudioEngine:
    def __init__(self, config: Config):
        self.config = config
        self._recording: subprocess.Popen[bytes] | None = None

    def play(self, path: Path, stop_check: StopCheck) -> Event:
        """Play a WAV file. Return the event that interrupted it, if any."""
        if not path.exists():
            LOG.warning("No s'ha trobat l'àudio opcional: %s", path)
            return Event.NONE

        LOG.info("Reproduint %s", path.name)
        proc = subprocess.Popen(
            [
                "aplay",
                "-q",
                "-D",
                self.config.playback_device,
                str(path),
            ]
        )
        try:
            while proc.poll() is None:
                event = stop_check()
                if event is not Event.NONE:
                    self._terminate(proc)
                    return event
                time.sleep(0.02)
            if proc.returncode:
                raise RuntimeError(f"aplay ha acabat amb codi {proc.returncode}")
            return Event.NONE
        except Exception:
            self._terminate(proc)
            raise

    def start_recording(self, temporary_path: Path) -> None:
        temporary_path.parent.mkdir(parents=True, exist_ok=True)
        LOG.info("Gravant temporalment a %s", temporary_path.name)
        self._recording = subprocess.Popen(
            [
                "arecord",
                "-q",
                "-D",
                self.config.capture_device,
                "-t",
                "wav",
                "-f",
                "S16_LE",
                "-r",
                str(self.config.sample_rate),
                "-c",
                str(self.config.channels),
                str(temporary_path),
            ]
        )

    def stop_recording(self) -> None:
        if self._recording is not None:
            self._terminate(self._recording, recording=True)
            self._recording = None

    @staticmethod
    def _terminate(
        proc: subprocess.Popen[bytes], *, recording: bool = False
    ) -> None:
        if proc.poll() is not None:
            return
        # SIGINT lets arecord finalize the WAV header before exiting.
        if recording:
            proc.send_signal(signal.SIGINT)
        else:
            proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=1)

    def close(self) -> None:
        self.stop_recording()

