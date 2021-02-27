#!/usr/bin/env python3

import os

from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path

import bot.utils.Database as Database
import bot.utils.Questions as Questions
from bot.utils.Logger import logger, setup_logger


if __name__ == '__main__':
    setup_logger(True, '')

    # Get current time and weekday.
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    schedule_day = now.strftime("%A")
    # Get the users with an active schedule, which was not yet triggered.
    users = Database.get_users_with_schedule(day=schedule_day, time=time_str)
    if not users:
        exit(0)

    # Initialize the chat service.
    credentials_dir = Path('/root/credentials')
    credentials = service_account.Credentials.from_service_account_file(
        credentials_dir / os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'],
        scopes=['https://www.googleapis.com/auth/chat.bot'])
    chat = build('chat', 'v1', credentials=credentials)

    # Send the standup message.
    for name, google_id, space in users:
        if not space:
            continue
        logger.info(f"Trigger for user: {name}, {google_id}, {space}")
        Database.reset_standup(google_id=google_id)
        response = chat.spaces().messages().create(
            parent=space,
            body={'text': Questions.get_standup_question(name, '0_na')}
        ).execute()
        logger.debug(f"Response: {response}")
