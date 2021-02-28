import os

from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path


def get_chat_service():
    # Initialize the chat service.
    credentials_dir = Path('/root/credentials')
    credentials = service_account.Credentials.from_service_account_file(
        credentials_dir / os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', ''),
        scopes=['https://www.googleapis.com/auth/chat.bot'])
    return build('chat', 'v1', credentials=credentials)
