from __future__ import annotations

import logging
import time
from enum import Enum, auto
from pathlib import Path

from .audio import AudioEngine
from .config import Config
from .events import Event
from .hardware import Hardware
from .storage import RecordingStore

LOG = logging.getLogger(__name__)


class State(Enum):
    ON_HOOK = auto()
    MENU = auto()
    CATEGORY = auto()
    RECORDING = auto()
    PLAYING = auto()


class Controller:
    def __init__(
        self,
        config: Config,
        hardware: Hardware,
        audio: AudioEngine,
        store: RecordingStore,
    ):
        self.config = config
        self.hardware = hardware
        self.audio = audio
        self.store = store
        self.state = State.ON_HOOK
        self.running = True
        self.category_stores = [
            RecordingStore(config.recordings_dir / category.slug, config.minimum_recording_seconds)
            for category in config.categories
        ]

    def run(self) -> None:
        LOG.info("Sistema preparat. Esperant que es despengi l'auricular.")
        while self.running:
            if self.hardware.on_hook:
                self.state = State.ON_HOOK
                self._wait_for_lift()
            else:
                self._menu_session()

    def _wait_for_lift(self) -> None:
        while self.running and self.hardware.on_hook:
            if self.hardware.poll(0.1) is Event.QUIT:
                self.running = False

    def _menu_session(self) -> None:
        while self.running and not self.hardware.on_hook:
            self.state = State.MENU
            interrupted = self._play_prompt("menu.wav", {Event.HUNG_UP})
            if interrupted is Event.HUNG_UP:
                return

            event = self._wait_for({Event.RECORD, Event.PLAY, Event.HUNG_UP})
            if event is Event.HUNG_UP:
                return
            if event not in {Event.RECORD, Event.PLAY}:
                return
            action = event
            if not self._select_category():
                return
            if action is Event.RECORD:
                if self._record_message() is Event.HUNG_UP:
                    return
            elif action is Event.PLAY:
                if self._play_random_message() is Event.HUNG_UP:
                    return

    def _select_category(self) -> bool:
        self.state = State.CATEGORY
        LOG.info("Selecciona la categoria: %s", "; ".join(
            f"{i}: {category.label}" for i, category in enumerate(self.config.categories, 1)
        ))
        # Accept a selection during the prompt too, without losing the press.
        accepted = {Event[f"CATEGORY_{i}"] for i in range(1, 8)}
        event = self._play_prompt("categories.wav", accepted | {Event.HUNG_UP})
        if event is Event.NONE:
            event = self._wait_for(accepted | {Event.HUNG_UP})
        if event not in accepted or not self.running or self.hardware.on_hook:
            return False
        index = int(event.name.rsplit("_", 1)[1]) - 1
        self.store = self.category_stores[index]
        LOG.info("Categoria seleccionada: %s", self.config.categories[index].label)
        return True

    def _record_message(self) -> Event:
        self.state = State.RECORDING
        if self._play_prompt("record_start.wav", {Event.HUNG_UP}) is Event.HUNG_UP:
            return Event.HUNG_UP
        if self._play_prompt("beep.wav", {Event.HUNG_UP}) is Event.HUNG_UP:
            return Event.HUNG_UP

        temporary = self.store.new_temporary_path()
        self.audio.start_recording(temporary)
        started = time.monotonic()
        end_event = Event.NONE
        try:
            while True:
                event = self.hardware.poll(0.05)
                if event is Event.HUNG_UP:
                    end_event = event
                    break
                if event is Event.RECORD and self.config.record_button_stops_recording:
                    break
                if event is Event.QUIT:
                    self.running = False
                    end_event = event
                    break
                if time.monotonic() - started >= self.config.max_recording_seconds:
                    LOG.info("S'ha arribat al límit de gravació.")
                    break
        finally:
            self.audio.stop_recording()

        saved = self.store.commit(temporary)
        if saved:
            LOG.info("Gravació desada: %s", saved.name)
        else:
            LOG.info("Gravació descartada perquè era massa curta o no era vàlida.")

        if end_event is Event.HUNG_UP or self.hardware.on_hook:
            return Event.HUNG_UP
        if end_event is Event.QUIT:
            return Event.QUIT

        prompt = "record_saved.wav" if saved else "record_too_short.wav"
        return self._play_prompt(prompt, {Event.HUNG_UP})

    def _play_random_message(self) -> Event:
        self.state = State.PLAYING
        selected = self.store.random_recording(
            avoid_repeat=self.config.avoid_immediate_repeat
        )
        if selected is None:
            return self._play_prompt("no_recordings.wav", {Event.HUNG_UP})

        stop_events = {Event.HUNG_UP}
        if self.config.play_button_stops_playback:
            stop_events.add(Event.PLAY)
        event = self._play_file(selected, stop_events)
        return Event.HUNG_UP if event is Event.HUNG_UP else Event.NONE

    def _play_prompt(self, filename: str, stop_events: set[Event]) -> Event:
        return self._play_file(self.config.sounds_dir / filename, stop_events)

    def _play_file(self, path: Path, stop_events: set[Event]) -> Event:
        def check() -> Event:
            if self.hardware.on_hook:
                return Event.HUNG_UP
            event = self.hardware.poll(0.01)
            if event is Event.QUIT:
                self.running = False
                return event
            return event if event in stop_events else Event.NONE

        return self.audio.play(path, check)

    def _wait_for(self, accepted: set[Event]) -> Event:
        while self.running:
            if self.hardware.on_hook:
                return Event.HUNG_UP
            event = self.hardware.poll(0.1)
            if event is Event.QUIT:
                self.running = False
                return event
            if event in accepted:
                return event
        return Event.QUIT

    def close(self) -> None:
        self.audio.close()
        self.hardware.close()

