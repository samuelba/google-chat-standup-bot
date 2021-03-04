#!/usr/bin/env python3

from datetime import datetime

import bot.utils.Chat as Chat
import bot.utils.Database as Database
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
    for user in users:
        if not user.space:
            continue
        logger.info(f"Trigger for user: {user.name}, {user.google_id}, {user.space}")
        Database.reset_standup(google_id=user.google_id)
        next_question = Database.get_current_question(google_id=user.google_id)
        if next_question is None:
            text = f"🤕 Sorry, I could not find a standup question. " \
                   f"Add new questions with `/add_question QUESTION`."
        else:
            text = f"*Hi {user.name}!*\nIt is standup time.\n\n" \
                   f"_{next_question.question}_"

        response = chat.spaces().messages().create(
            parent=user.space,
            body={'text': text}
        ).execute()
        logger.debug(f"Response: {response}")
