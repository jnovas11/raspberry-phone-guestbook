import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

from phone_guestbook.config import Config
from phone_guestbook.controller import Controller
from phone_guestbook.events import Event
from phone_guestbook.storage import RecordingStore
from test_storage import create_wav


class CategoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        config_path = Path(__file__).resolve().parents[1] / 'config.ini'
        self.config = replace(Config.load(config_path), recordings_dir=Path(self.temp.name))
        self.hardware = Mock(on_hook=False)
        self.audio = Mock()
        self.controller = Controller(self.config, self.hardware, self.audio,
                                     RecordingStore(self.config.recordings_dir, 1))

    def test_all_seven_positions_select_their_folder(self):
        for index, category in enumerate(self.config.categories, 1):
            self.audio.play.return_value = Event[f'CATEGORY_{index}']
            self.assertTrue(self.controller._select_category())
            self.assertEqual(self.controller.store.directory.name, category.slug)

    def test_playback_is_isolated_to_selected_category(self):
        first, second = self.controller.category_stores[:2]
        create_wav(first.directory / 'first.wav', 2)
        self.assertIsNone(second.random_recording())
        self.assertEqual(first.random_recording().name, 'first.wav')

    def test_hangup_cancels_category_selection(self):
        self.audio.play.return_value = Event.HUNG_UP
        self.assertFalse(self.controller._select_category())

    def test_quit_cancels_category_selection(self):
        self.audio.play.return_value = Event.NONE
        self.hardware.poll.return_value = Event.QUIT
        self.assertFalse(self.controller._select_category())
        self.assertFalse(self.controller.running)

    def test_action_is_kept_until_category_selection(self):
        self.controller._play_prompt = Mock(return_value=Event.NONE)
        self.controller._wait_for = Mock(side_effect=[Event.RECORD, Event.QUIT])
        self.controller._select_category = Mock(return_value=True)
        self.controller._record_message = Mock(return_value=Event.HUNG_UP)
        self.controller._menu_session()
        self.controller._record_message.assert_called_once()


if __name__ == '__main__':
    unittest.main()
