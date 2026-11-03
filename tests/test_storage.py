import tempfile
import unittest
import wave
from pathlib import Path

from phone_guestbook.storage import RecordingStore


def create_wav(path: Path, seconds: float, rate: int = 8000) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        wav_file.writeframes(b"\x00\x00" * int(rate * seconds))


class RecordingStoreTests(unittest.TestCase):
    def test_commit_renames_valid_recording(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RecordingStore(Path(directory), minimum_seconds=1.0)
            temporary = store.new_temporary_path()
            create_wav(temporary, 1.5)
            final = store.commit(temporary)
            self.assertIsNotNone(final)
            self.assertTrue(final.exists())
            self.assertFalse(temporary.exists())

    def test_commit_discards_short_recording(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RecordingStore(Path(directory), minimum_seconds=1.0)
            temporary = store.new_temporary_path()
            create_wav(temporary, 0.25)
            self.assertIsNone(store.commit(temporary))
            self.assertFalse(temporary.exists())

    def test_random_recording_ignores_invalid_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = RecordingStore(root, minimum_seconds=1.0)
            create_wav(root / "valid.wav", 2.0)
            (root / "broken.wav").write_bytes(b"not a wav")
            self.assertEqual(store.random_recording(), root / "valid.wav")


if __name__ == "__main__":
    unittest.main()

