from __future__ import annotations

import time
from typing import Protocol

from .config import Config
from .events import Event


class Hardware(Protocol):
    @property
    def on_hook(self) -> bool: ...

    def poll(self, timeout: float = 0.05) -> Event: ...

    def close(self) -> None: ...


class GPIOHardware:
    """GPIO adapter. All switches connect their configured GPIO to GND."""

    def __init__(self, config: Config):
        try:
            from gpiozero import Button
        except ImportError as exc:
            raise RuntimeError(
                "Falta gpiozero. Instal·la el paquet o executa amb --simulate."
            ) from exc

        kwargs = {
            "pull_up": True,
            "bounce_time": config.bounce_seconds,
        }
        self._hook = Button(config.hook_pin, **kwargs)
        self._record = Button(config.record_button_pin, **kwargs)
        self._play = Button(config.play_button_pin, **kwargs)
        self._categories = [Button(category.pin, **kwargs) for category in config.categories]
        self._last_categories = [button.is_pressed for button in self._categories]
        self._hook_on_hook_when_active = config.hook_on_hook_when_active

        self._last_on_hook = self.on_hook
        self._last_record = self._record.is_pressed
        self._last_play = self._play.is_pressed

    @property
    def on_hook(self) -> bool:
        active = self._hook.is_pressed
        return active if self._hook_on_hook_when_active else not active

    def poll(self, timeout: float = 0.05) -> Event:
        deadline = time.monotonic() + timeout
        while True:
            on_hook = self.on_hook
            record = self._record.is_pressed
            play = self._play.is_pressed
            categories = [button.is_pressed for button in self._categories]

            event = Event.NONE
            if on_hook != self._last_on_hook:
                event = Event.HUNG_UP if on_hook else Event.LIFTED
            elif record and not self._last_record:
                event = Event.RECORD
            elif play and not self._last_play:
                event = Event.PLAY
            else:
                for index, pressed in enumerate(categories):
                    if pressed and not self._last_categories[index]:
                        event = Event[f"CATEGORY_{index + 1}"]
                        break

            self._last_on_hook = on_hook
            self._last_record = record
            self._last_play = play
            self._last_categories = categories

            if event is not Event.NONE or time.monotonic() >= deadline:
                return event
            time.sleep(0.01)

    def close(self) -> None:
        self._hook.close()
        self._record.close()
        self._play.close()
        for button in self._categories:
            button.close()

