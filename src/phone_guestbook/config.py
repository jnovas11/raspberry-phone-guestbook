from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Category:
    slug: str
    label: str
    pin: int


@dataclass(frozen=True)
class Config:
    project_dir: Path
    hook_pin: int
    record_button_pin: int
    play_button_pin: int
    hook_on_hook_when_active: bool
    bounce_seconds: float
    capture_device: str
    playback_device: str
    sample_rate: int
    channels: int
    max_recording_seconds: float
    minimum_recording_seconds: float
    recordings_dir: Path
    sounds_dir: Path
    record_button_stops_recording: bool
    play_button_stops_playback: bool
    avoid_immediate_repeat: bool
    categories: tuple[Category, ...]

    @classmethod
    def load(cls, path: Path) -> "Config":
        path = path.resolve()
        parser = ConfigParser()
        if not parser.read(path, encoding="utf-8"):
            raise FileNotFoundError(f"No s'ha trobat la configuració: {path}")

        base = path.parent

        def relative_path(value: str) -> Path:
            candidate = Path(value)
            return candidate if candidate.is_absolute() else base / candidate

        categories = tuple(
            Category(
                slug=parser.get(f"category_{i}", "folder"),
                label=parser.get(f"category_{i}", "name"),
                pin=parser.getint(f"category_{i}", "pin"),
            )
            for i in range(1, 8)
        )
        pins = [parser.getint("gpio", key) for key in
                ("hook_pin", "record_button_pin", "play_button_pin")]
        pins.extend(category.pin for category in categories)
        if len(pins) != len(set(pins)) or any(pin < 0 or pin > 27 for pin in pins):
            raise ValueError("Els GPIO han de ser únics i estar entre 0 i 27.")
        for category in categories:
            if not category.slug or not all(c in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in category.slug):
                raise ValueError("Nom de carpeta de categoria no vàlid.")
        if len({category.slug for category in categories}) != 7:
            raise ValueError("Les categories han de tenir carpetes diferents.")

        return cls(
            categories=categories,
            project_dir=base,
            hook_pin=parser.getint("gpio", "hook_pin"),
            record_button_pin=parser.getint("gpio", "record_button_pin"),
            play_button_pin=parser.getint("gpio", "play_button_pin"),
            hook_on_hook_when_active=parser.getboolean(
                "gpio", "hook_on_hook_when_active"
            ),
            bounce_seconds=parser.getfloat("gpio", "bounce_seconds"),
            capture_device=parser.get("audio", "capture_device"),
            playback_device=parser.get("audio", "playback_device"),
            sample_rate=parser.getint("audio", "sample_rate"),
            channels=parser.getint("audio", "channels"),
            max_recording_seconds=parser.getfloat(
                "audio", "max_recording_seconds"
            ),
            minimum_recording_seconds=parser.getfloat(
                "audio", "minimum_recording_seconds"
            ),
            recordings_dir=relative_path(parser.get("paths", "recordings")),
            sounds_dir=relative_path(parser.get("paths", "sounds")),
            record_button_stops_recording=parser.getboolean(
                "behaviour", "record_button_stops_recording"
            ),
            play_button_stops_playback=parser.getboolean(
                "behaviour", "play_button_stops_playback"
            ),
            avoid_immediate_repeat=parser.getboolean(
                "behaviour", "avoid_immediate_repeat"
            ),
        )

