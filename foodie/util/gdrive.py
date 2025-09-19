#!/usr/bin/env python3
"""
Google Drive File Uploader and Sharer
Uploads a file to Google Drive and makes it shareable with anyone who has the link
"""

import os
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path


# Scopes needed for uploading and sharing files
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class Uploader:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Initialize Google Drive uploader

        Args:
            credentials_file: Path to credentials.json from Google Cloud Console
            token_file: Path where to store the access token
        """
        self.credentials_file = str(Path(Path(__file__).parent, credentials_file))
        self.token_file = str(Path(Path(__file__).parent, token_file))
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None

        # Check if we have a saved token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"Error: {self.credentials_file} not found!")
                    print("Download it from Google Cloud Console")
                    sys.exit(1)

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        # Build the service
        self.service = build('drive', 'v3', credentials=creds)
        print("✓ Successfully authenticated with Google Drive")

    def upload_file(self, file_path, drive_filename=None, folder_id=None):
        """
        Upload a file to Google Drive

        Args:
            file_path: Local path to the file
            drive_filename: Name for the file in Drive (optional)
            folder_id: Google Drive folder ID to upload to (optional)

        Returns:
            File ID of uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Use original filename if not specified
        if not drive_filename:
            drive_filename = os.path.basename(file_path)

        print(f"Uploading {file_path} as '{drive_filename}'...")

        # File metadata
        file_metadata = {'name': drive_filename}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        # Create media upload object
        media = MediaFileUpload(file_path, resumable=True)

        # Upload the file
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = file.get('id')
        print(f"✓ File uploaded successfully! File ID: {file_id}")
        return file_id

    def share_with_anyone(self, file_id, role='reader'):
        """
        Share a file with anyone who has the link

        Args:
            file_id: Google Drive file ID
            role: Permission level ('reader', 'writer', 'commenter')

        Returns:
            Shareable link
        """
        print(f"Making file shareable with role: {role}")

        # Create permission for anyone with the link
        permission = {
            'role': role,
            'type': 'anyone'
        }

        # Apply the permission
        self.service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()

        # Get the shareable link
        file_info = self.service.files().get(
            fileId=file_id,
            fields='webViewLink,webContentLink'
        ).execute()

        view_link = file_info.get('webViewLink')
        download_link = file_info.get('webContentLink')

        print(f"✓ File is now shareable!")
        print(f"View link: {view_link}")
        if download_link:
            print(f"Download link: {download_link}")

        return view_link

    def upload_and_share(self, file_path, drive_filename=None, role='reader', folder_id=None):
        """
        Upload a file and immediately share it

        Args:
            file_path: Local file path
            drive_filename: Name in Drive (optional)
            role: Permission level ('reader', 'writer', 'commenter')
            folder_id: Folder to upload to (optional)

        Returns:
            Dictionary with file_id and share_link
        """
        try:
            # Upload the file
            file_id = self.upload_file(file_path, drive_filename, folder_id)

            # Share it
            share_link = self.share_with_anyone(file_id, role)

            return {
                'file_id': file_id,
                'share_link': share_link,
                'success': True
            }

        except Exception as e:
            print(f"Error: {e}")
            return {
                'error': str(e),
                'success': False
            }
