import unittest
from foodie.util.surge_util import upload_to_surge
from pathlib import Path


class TestSurgeUtil(unittest.TestCase):
    def setUp(self):
        self.file_path = str(Path(Path(__file__).parent, 'temp_map.html'))

    def test_upload(self):

        upload_to_surge(self.file_path)


if __name__ == '__main__':
    unittest.main()
