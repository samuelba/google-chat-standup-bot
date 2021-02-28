#!/usr/bin/env python3

from datetime import datetime

import bot.utils.Chat as Chat
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
    chat = Chat.get_chat_service()

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
