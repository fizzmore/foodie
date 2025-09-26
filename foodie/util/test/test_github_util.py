import unittest
from foodie.util.github_util import GitHubUploader
import os
from pathlib import Path
from dotenv import load_dotenv


class TestGithubUtil(unittest.TestCase):

    def setUp(self):
        # Configuration - UPDATE THESE VALUES
        load_dotenv(Path(Path(__file__).parents[2], '.env'))
        github_token = os.getenv('FIZZ_GITHUB')
        username = "fizzmore"  # Your GitHub username
        repo_name = "foodie"  # Your repository name

        self.uploader = GitHubUploader(github_token, username, repo_name)

    def test_login(self):
        self.uploader.test_connection()

    def test_upload_file(self):
        self.uploader.upload_file(str(Path(Path(__file__).parent, 'temp_map.html')),
                                  repo_file_path='docs/temp_map.html')

    def test_delete_file(self):
        self.uploader.delete_file('docs/temp_map.html')

if __name__ == '__main__':
    unittest.main()
