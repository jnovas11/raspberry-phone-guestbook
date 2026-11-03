from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .audio import AudioEngine
from .config import Config
from .controller import Controller
from .hardware import GPIOHardware
from .simulator import ConsoleHardware, SimulatedAudioEngine
from .storage import RecordingStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Llibre de visites d'àudio")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.ini"),
        help="Fitxer de configuració (per defecte: config.ini)",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Prova amb el teclat, sense GPIO ni targeta de so",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = Config.load(args.config)
    store = RecordingStore(
        config.recordings_dir, config.minimum_recording_seconds
    )

    if args.simulate:
        hardware = ConsoleHardware()
        audio = SimulatedAudioEngine(config)
    else:
        hardware = GPIOHardware(config)
        audio = AudioEngine(config)

    controller = Controller(config, hardware, audio, store)
    try:
        controller.run()
    except KeyboardInterrupt:
        pass
    finally:
        controller.close()


if __name__ == "__main__":
    main()

