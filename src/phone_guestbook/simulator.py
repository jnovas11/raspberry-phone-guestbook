from __future__ import annotations

import logging
import queue
import sys
import threading
import time
import wave
from pathlib import Path

from .config import Config
from .events import Event

LOG = logging.getLogger(__name__)


class ConsoleHardware:
    """Keyboard-driven hardware replacement for development on any computer."""

    def __init__(self):
        self._on_hook = True
        self._events: queue.Queue[Event] = queue.Queue()
        self._closed = False
        self._thread = threading.Thread(target=self._read_commands, daemon=True)
        self._thread.start()

    @property
    def on_hook(self) -> bool:
        return self._on_hook

    def _read_commands(self) -> None:
        print("Simulador: h=penjar/despenjar, r=gravar, p=reproduir, 1–7=categoria, q=sortir")
        while not self._closed:
            try:
                command = input("> ").strip().lower()
            except EOFError:
                command = "q"
            if command == "h":
                self._on_hook = not self._on_hook
                event = Event.HUNG_UP if self._on_hook else Event.LIFTED
                print("Auricular penjat" if self._on_hook else "Auricular despenjat")
                self._events.put(event)
            elif command == "r":
                self._events.put(Event.RECORD)
            elif command == "p":
                self._events.put(Event.PLAY)
            elif command in ("1", "2", "3", "4", "5", "6", "7"):
                self._events.put(Event[f"CATEGORY_{command}"])
            elif command == "q":
                self._events.put(Event.QUIT)
                return

    def poll(self, timeout: float = 0.05) -> Event:
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return Event.NONE

    def close(self) -> None:
        self._closed = True


class SimulatedAudioEngine:
    def __init__(self, config: Config):
        self.config = config
        self._temporary_path: Path | None = None
        self._recording_started = 0.0

    def play(self, path: Path, stop_check) -> Event:
        exists = path.exists()
        label = path.name if exists else f"{path.name} (encara no creat)"
        LOG.info("[SIMULACIÓ] Reproduint %s", label)

        duration = self._wav_duration(path) if exists else 1.0
        playing_on_windows = exists and sys.platform == "win32"
        if playing_on_windows:
            import winsound

            winsound.PlaySound(
                str(path), winsound.SND_FILENAME | winsound.SND_ASYNC
            )

        deadline = time.monotonic() + duration
        try:
            while time.monotonic() < deadline:
                event = stop_check()
                if event is not Event.NONE:
                    return event
                time.sleep(0.02)
            return Event.NONE
        finally:
            if playing_on_windows:
                import winsound

                winsound.PlaySound(None, winsound.SND_PURGE)

    @staticmethod
    def _wav_duration(path: Path) -> float:
        try:
            with wave.open(str(path), "rb") as wav_file:
                return wav_file.getnframes() / wav_file.getframerate()
        except (OSError, EOFError, wave.Error, ZeroDivisionError):
            return 1.0

    def start_recording(self, temporary_path: Path) -> None:
        LOG.info("[SIMULACIÓ] Gravació iniciada")
        self._temporary_path = temporary_path
        self._recording_started = time.monotonic()

    def stop_recording(self) -> None:
        if self._temporary_path is None:
            return
        seconds = max(0.1, time.monotonic() - self._recording_started)
        frames = int(seconds * self.config.sample_rate)
        self._temporary_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(self._temporary_path), "wb") as wav_file:
            wav_file.setnchannels(self.config.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.config.sample_rate)
            wav_file.writeframes(b"\x00\x00" * frames * self.config.channels)
        self._temporary_path = None

    def close(self) -> None:
        self.stop_recording()
