from datetime import date
from flask import json
from typing import Any

import bot.utils.Cards as Cards
import bot.utils.Chat as Chat
import bot.utils.Team as Team
import bot.utils.User as User
import bot.utils.storage.Storage as Storage
from bot.utils.Logger import logger


def handle_event(event, user: User, space: str, is_room: bool) -> Any:
    # Join team.
    if event['action']['actionMethodName'] == 'join_team':
        return join_team(event, user, space, is_room)
    # Remove team.
    if event['action']['actionMethodName'] == 'remove_team':
        return remove_team(event)
    # Send the standup answers to the team room.
    if event['action']['actionMethodName'] == 'send_answers':
        return send_standup_answers_to_room(user, is_room)
    # Enable/disable schedule.
    if event['action']['actionMethodName'] == 'enable_schedule':
        return enable_schedule(event, user)
    # Remove question.
    if event['action']['actionMethodName'] == 'remove_question':
        return remove_question(event, user)
    # Reorder questions.
    if event['action']['actionMethodName'] == 'reorder_questions':
        return reorder_questions(event, user)


def join_team(event, user: User, space: str, is_room: bool) -> str:
    team_name = event['action']['parameters'][0]['value']
    if is_room:
        if Storage.join_room_to_team(team_name=team_name, space=space):
            text = f"This room has joined the team '{team_name}'."
        else:
            text = f"🤕 Sorry, I couldn't add this room to the team '{team_name}'"
    else:
        if Storage.join_team(google_id=user.google_id, team_name=team_name):
            text = f"You have joined the team '{team_name}'."
        else:
            text = f"🤕 Sorry, I couldn't add you to the team '{team_name}'"
    return json.jsonify({'text': text})


def remove_team(event) -> Any:
    team_name = event['action']['parameters'][0]['value']
    if Storage.remove_team(team_name=team_name):
        text = f"I successfully removed the team '{team_name}'."
    else:
        text = f"🤕 Sorry, I couldn't remove the team '{team_name}'."
    teams = Storage.get_teams()
    message = Cards.get_team_remove_card(teams, True)
    message['text'] = text
    return json.jsonify(message)


def send_standup_card(card, user: User, team: Team):
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    chat = Chat.get_chat_service()
    response = chat.spaces().messages().create(
        parent=team.space,
        threadKey=today_str,
        body={
            'text': f"I just received the standup answers from *{user.name}*:",
            'cards': [card]
        }
    ).execute()
    logger.debug(f"Response: {response}")
    message_id = response['name']
    logger.debug(f"Message id: {message_id}")
    Storage.set_message_id(google_id=user.google_id, message_id=message_id)


def update_standup_card(card, user: User, message_id: str):
    chat = Chat.get_chat_service()
    logger.info(f"message id: {message_id}")
    response = chat.spaces().messages().update(
        name=message_id,
        updateMask='cards,text',
        body={
            'text': f"I just received the standup answers from *{user.name}* (updated):",
            'cards': [card]
        }
    ).execute()
    logger.debug(f"Response (update card): {response}")


def send_standup_answers_to_room(user: User, is_room: bool) -> str:
    if is_room:
        text = "🤕 Sorry, something went wrong."
    else:
        logger.info("Publish to the team room.")
        answers = Storage.get_standup_answers(google_id=user.google_id)
        message_id = Storage.get_standup_answer_message_id(google_id=user.google_id)
        card = Cards.get_standup_card(user, answers, False)
        team = Storage.get_team_of_user(google_id=user.google_id)
        logger.info(f"Message id: {message_id}")
        if team:
            if team.space:
                if message_id:
                    update_standup_card(card, user, message_id)
                    text = "Your standup answers have been updated in your team room."
                else:
                    send_standup_card(card, user, team)
                    text = "Your standup answers have been published in your team room."
            else:
                text = "🤕 Sorry, your team room does either not have the standup bot " \
                       "and/or did not yet join a team. Add the standup bot to your team room " \
                       "and run `/join_team` in your team room to join a team."
        else:
            text = "🤕 Sorry, you did not yet join a team. Use `/join_team` to join a team."
    return json.jsonify({'text': text})


def enable_schedule(event, user: User) -> Any:
    day = event['action']['parameters'][0]['value']
    enable = event['action']['parameters'][1]['value'] == 'True'
    if Storage.enable_schedule(google_id=user.google_id, day=day, enable=enable):
        text = f"I {'enabled' if enable else 'disabled'} successfully the schedule for {day}."
    else:
        text = f"🤕 Sorry, I couldn't {'enable' if enable else 'disable'} the schedule for {day}."
    schedules = Storage.get_schedules(google_id=user.google_id)
    message = Cards.get_schedule_enable_card(schedules, True)
    message['text'] = text
    return json.jsonify(message)


def remove_question(event, user: User) -> Any:
    question_id = int(event['action']['parameters'][0]['value'])
    question = event['action']['parameters'][1]['value']
    if Storage.remove_question(question_id=question_id):
        text = f"I removed successfully the question '{question}'."
    else:
        text = f"🤕 Sorry, I couldn't remove the question '{question}'"
    questions = Storage.get_questions(google_id=user.google_id)
    message = Cards.get_question_remove_card(questions, True)
    message['text'] = text
    return json.jsonify(message)


def reorder_questions(event, user) -> Any:
    question_id = int(event['action']['parameters'][0]['value'])
    question = event['action']['parameters'][1]['value']
    order_step = int(event['action']['parameters'][2]['value'])
    team_id = int(event['action']['parameters'][3]['value'])
    logger.info(f"Question id: {question_id}")
    logger.info(f"Question: {question}")
    logger.info(f"Order step: {order_step}")

    Storage.reorder_questions(team_id=team_id, question_id=question_id, order_step=order_step)
    questions = Storage.get_questions(google_id=user.google_id)
    return json.jsonify(Cards.get_question_reorder_card(questions, order_step + 1))
