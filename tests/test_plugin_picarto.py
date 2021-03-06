import unittest

from livecli.plugins.picarto import Picarto


class TestPluginPicarto(unittest.TestCase):
    def test_can_handle_url(self):
        should_match = [
            'https://picarto.tv/example',
        ]
        for url in should_match:
            self.assertTrue(Picarto.can_handle_url(url))

        should_not_match = [
            'https://example.com/index.html',
        ]
        for url in should_not_match:
            self.assertFalse(Picarto.can_handle_url(url))
