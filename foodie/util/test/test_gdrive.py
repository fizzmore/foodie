import unittest
from foodie.util.gdrive import Uploader
from pathlib import Path


class TestGDrive(unittest.TestCase):
    def test_login(self):
        # We want to see "✓ Successfully authenticated with Google Drive" message
        Uploader()

    def test_upload_file(self):
        uploader = Uploader()
        uploader.upload_and_share(str(Path(Path(__file__).parent, 'temp_map.html')))


if __name__ == '__main__':
    unittest.main()
