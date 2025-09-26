import os
import sys
import requests
import base64
import json
from datetime import datetime
from pathlib import Path


class GitHubUploader:
    def __init__(self, github_token, username, repo_name):
        """Initialize GitHub uploader"""
        self.token = github_token
        self.username = username
        self.repo = repo_name
        self.api_base = f"https://api.github.com/repos/{username}/{repo_name}"
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }

        print(f"🚀 GitHub HTML Uploader initialized")
        print(f"📂 Repository: {username}/{repo_name}")

    def test_connection(self):
        """Test if repository exists and token is valid"""
        try:
            response = requests.get(self.api_base, headers=self.headers)
            if response.status_code == 200:
                repo_info = response.json()
                print(f"✅ Connection successful!")
                print(f"📊 Repository: {repo_info['full_name']}")
                print(f"🌐 GitHub Pages URL: https://{self.username}.github.io/{self.repo}/")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def file_exists(self, file_path):
        """Check if file already exists in repository"""
        url = f"{self.api_base}/contents/{file_path}"
        response = requests.get(url, headers=self.headers)
        return response.status_code == 200, response.json() if response.status_code == 200 else None

    def upload_file(self, local_file_path, repo_file_path=None, commit_message=None):
        """Upload HTML file to GitHub repository"""
        if not os.path.exists(local_file_path):
            return {'error': f'Local file not found: {local_file_path}'}

        # Set repository path
        if not repo_file_path:
            repo_file_path = os.path.basename(local_file_path)

        # Read HTML content
        try:
            with open(local_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            return {'error': f'Failed to read file: {e}'}

        # Encode content
        content_encoded = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')

        # Check if file exists
        exists, existing_file = self.file_exists(repo_file_path)

        # Prepare commit data
        if not commit_message:
            action = "Update" if exists else "Add"
            commit_message = f"{action} HTML file: {repo_file_path}"

        commit_data = {
            "message": commit_message,
            "content": content_encoded
        }

        # Add SHA if file exists (for updates)
        if exists:
            commit_data["sha"] = existing_file["sha"]
            print(f"🔄 Updating existing file: {repo_file_path}")
        else:
            print(f"📤 Uploading new file: {repo_file_path}")

        # Upload file
        url = f"{self.api_base}/contents/{repo_file_path}"
        response = requests.put(url, headers=self.headers, json=commit_data)

        if response.status_code in [200, 201]:
            result = response.json()

            # Generate URLs
            urls = {
                'github_url': result['content']['html_url'],
                'raw_url': result['content']['download_url'],
                'pages_url': f"https://{self.username}.github.io/{self.repo}/{repo_file_path}",
                'api_url': result['content']['url']
            }

            print(f"✅ Upload successful!")
            print(f"📊 File: {repo_file_path}")
            print(f"🌐 Live URL: {urls['pages_url']}")

            return {
                'success': True,
                'file_path': repo_file_path,
                'urls': urls,
                'commit': result['commit']
            }
        else:
            return {
                'success': False,
                'error': f'Upload failed: {response.status_code}',
                'error_details': response.text
            }

    def delete_file(self, file_path, commit_message=None):
        """
        Delete a file from the GitHub repository

        Args:
            file_path: Path to file in repository (e.g., "map.html" or "maps/map1.html")
            It does not include the repository name
            commit_message: Custom commit message (optional)

        Returns:
            dict: Deletion result
        """
        print(f"🗑️  Attempting to delete: {file_path}")

        # Check if file exists
        exists, existing_file = self.file_exists(file_path)

        if not exists:
            return {'error': f'File not found: {file_path}'}

        # Prepare commit message
        if not commit_message:
            commit_message = f"Delete file: {file_path}"

        # Prepare deletion data
        delete_data = {
            "message": commit_message,
            "sha": existing_file["sha"]  # Required for deletion
        }

        # Delete file
        url = f"{self.api_base}/contents/{file_path}"
        response = requests.delete(url, headers=self.headers, json=delete_data)

        if response.status_code == 200:
            result = response.json()

            print(f"✅ File deleted successfully!")
            print(f"🗑️  Removed: {file_path}")

            return {
                'success': True,
                'file_path': file_path,
                'commit': result['commit']
            }
        else:
            return {
                'error': f'Delete failed: {response.status_code}',
                'details': response.text
            }

    def delete_multiple_files(self, file_list):
        """
        Delete multiple files from repository

        Args:
            file_list: List of file paths to delete

        Returns:
            dict: Results for each file
        """
        results = {}

        for file_path in file_list:
            print(f"\n🗑️  Processing deletion: {file_path}")
            result = self.delete_file(file_path)
            results[file_path] = result

        return results


    def get_repository_files(self, path=""):
        """Get list of files in repository"""
        url = f"{self.api_base}/contents/{path}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            files = response.json()
            html_files = [f['name'] for f in files if f['name'].endswith('.html')]
            return html_files
        return []



