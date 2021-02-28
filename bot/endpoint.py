#!/usr/bin/env python3

import os

from datetime import date
from flask import Flask, request, json, Response, send_from_directory
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

import bot.utils.Cards as Cards
import bot.utils.Chat as Chat
import bot.utils.Database as Database
import bot.utils.Questions as Questions
from bot.utils.Logger import setup_logger
from bot.utils.Team import Team
from bot.utils.User import User
from bot.utils.Weekdays import Weekdays

app = Flask(__name__, static_url_path='')

CHAT_ISSUER = 'chat@system.gserviceaccount.com'
PUBLIC_CERT_URL_PREFIX = 'https://www.googleapis.com/service_accounts/v1/metadata/x509/'
AUDIENCE = os.environ.get('AUDIENCE', '')
NO_ANSWER = "🤔 Sorry, I don't have an answer for that."


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
    app.logger.debug(f"Response: {response}")
    message_id = response['name']
    app.logger.debug(f"Message id: {message_id}")
    Database.set_message_id(google_id=user.google_id, message_id=message_id)


def update_standup_card(card, user: User, team: Team, message_id: str):
    chat = Chat.get_chat_service()
    app.logger.info(f"message id: {message_id}")
    response = chat.spaces().messages().update(
        name=message_id,
        updateMask='cards,text',
        body={
            'text': f"I just received the standup answers from *{user.name}* (updated):",
            'cards': [card]
        }
    ).execute()
    app.logger.debug(f"Response (update card): {response}")


def get_user_from_event(event) -> User:
    google_id = event['user']['name']
    display_name = event['user']['displayName']
    email = event['user']['email']
    avatar_url = event['user']['avatarUrl']
    space = event['space']['name']
    return User(0, google_id, display_name, email, avatar_url, space, False, '')


@app.route('/api/v1/', methods=['POST'])
def on_event():
    """
    Handles an event from Google Chat.
    """

    # Check the authorization.
    app.logger.info(AUDIENCE)
    auth_header = request.headers.get('Authorization')
    auth_token = ''
    if auth_header:
        auth_token = auth_header.split(' ')[1]
    try:
        id_info = id_token.verify_token(auth_token, google_requests.Request(), AUDIENCE,
                                        certs_url=PUBLIC_CERT_URL_PREFIX + CHAT_ISSUER)
        if id_info['iss'] != CHAT_ISSUER:
            app.logger.error("Invalid issuer.")
            return Response("Unauthorized.", status=401)
    except ValueError:
        app.logger.error("Invalid credentials.")
        return Response("Unauthorized.", status=401)

    # Handle the request.
    event = request.get_json()
    text = ''
    user = get_user_from_event(event)
    is_room = event['space']['type'] == 'ROOM'
    space = event['space']['name']

    app.logger.info(f"The event: {event}")
    if event['type'] == 'ADDED_TO_SPACE':
        if not is_room:
            Database.add_user(user=user)
        teams = Database.get_teams()
        return json.jsonify(Cards.get_team_selection_card(teams, True))

    elif event['type'] == 'REMOVED_FROM_SPACE':
        if is_room:
            Database.remove_team_space(space=space)
        else:
            Database.disable_user(user=user)
            text = ""

    elif event['type'] == 'MESSAGE':
        if 'slashCommand' in event['message']:
            app.logger.debug(f"Slash command {event['message']['slashCommand']['commandId']}")
            # /add_team team_name
            if event['message']['slashCommand']['commandId'] == '1':
                team_name = ''
                if 'argumentText' in event['message']:
                    team_name = event['message']['argumentText'].strip(' "\'')
                if team_name and Database.add_team(team_name=team_name):
                    text = f"I successfully added the new team '{team_name}'."
                else:
                    text = f"🤕 Sorry, I couldn't add the new team '{team_name}'."
            # /teams
            if event['message']['slashCommand']['commandId'] == '3':
                teams = Database.get_teams()
                return json.jsonify(Cards.get_team_list_card(teams))
            # /join_team
            if event['message']['slashCommand']['commandId'] == '4':
                teams = Database.get_teams()
                return json.jsonify(Cards.get_team_selection_card(teams, False))
            # /users [team_name]
            if event['message']['slashCommand']['commandId'] == '5':
                team_name = ''
                if 'argumentText' in event['message']:
                    team_name = event['message']['argumentText'].strip(' "\'')
                users = Database.get_users(team_name=team_name)
                return json.jsonify(Cards.get_user_list_card(users))
            # /standup
            if event['message']['slashCommand']['commandId'] == '6':
                if is_room:
                    text = "🤕 Sorry, but this command has no effect in a room."
                else:
                    Database.reset_standup(google_id=user.google_id)
                    text = Questions.get_standup_question(user.name, '0_na')
            # /disable_schedule day
            if event['message']['slashCommand']['commandId'] == '7':
                if is_room:
                    text = "🤕 Sorry, but this command has no effect in a room."
                else:
                    schedule_day = ''
                    if 'argumentText' in event['message']:
                        schedule_day = event['message']['argumentText'].strip(' "\'').capitalize()
                    if schedule_day and schedule_day in Weekdays and \
                            Database.enable_schedule(google_id=user.google_id, day=schedule_day, enable=False):
                        text = f"Your standup schedule for '{schedule_day}' is disabled."
                    else:
                        text = f"🤕 Sorry, I couldn't disable your standup schedule for '{schedule_day}'. " \
                               f"Use e.g. `/disable_schedule monday`"
            # /enable_schedule day
            if event['message']['slashCommand']['commandId'] == '8':
                if is_room:
                    text = "🤕 Sorry, but this command has no effect in a room."
                else:
                    schedule_day = ''
                    if 'argumentText' in event['message']:
                        schedule_day = event['message']['argumentText'].strip(' "\'').capitalize()
                    if schedule_day and schedule_day in Weekdays and \
                            Database.enable_schedule(google_id=user.google_id, day=schedule_day, enable=True):
                        text = f"Your standup schedule for '{schedule_day}' is enabled."
                    else:
                        text = f"🤕 Sorry, I couldn't enable your standup schedule for '{schedule_day}'. " \
                               f"Use e.g. `/enable_schedule monday`"
            # /change_schedule_time day time
            if event['message']['slashCommand']['commandId'] == '9':
                if is_room:
                    text = "🤕 Sorry, but this command has no effect in a room."
                else:
                    schedule_day = ''
                    schedule_time = ''
                    if 'argumentText' in event['message']:
                        argument = event['message']['argumentText'].strip(' "\'')
                        arguments = argument.rsplit(' ')
                        if len(arguments) == 2:
                            schedule_day = arguments[0].strip(' "\'').capitalize()
                            schedule_time = arguments[1].strip(' "\'')
                    if schedule_time and schedule_day and schedule_day in Weekdays \
                            and Database.update_schedule_time(google_id=user.google_id, day=schedule_day,
                                                              time=schedule_time):
                        text = f"Your standup schedule time for '{schedule_day}' is now '{schedule_time}'."
                    else:
                        text = f"🤕 Sorry, I couldn't change your standup schedule time '{schedule_time}' " \
                               f"for '{schedule_day}'. Use e.g. `/change_schedule_time monday 09:00:00`"
            # /schedules
            if event['message']['slashCommand']['commandId'] == '10':
                if is_room:
                    text = "🤕 Sorry, but this command has no effect in a room."
                else:
                    schedules = Database.get_schedules(google_id=user.google_id)
                    return json.jsonify(Cards.get_schedule_list_card(schedules))

        # Handle standup answers and generic requests.
        else:
            if is_room:
                text = NO_ANSWER
            else:
                question_type = Database.get_standup_question_type(google_id=user.google_id)
                if question_type and question_type != '3_blocking':
                    answer = event['message']['text']
                    success, question_type = Database.add_standup_answer(google_id=user.google_id, answer=answer)
                    text = Questions.get_standup_question(user.name, question_type)
                    if question_type == '3_blocking':
                        app.logger.info("Publish to the team webhook.")
                        answers = Database.get_standup_answers(google_id=user.google_id)
                        card = Cards.get_standup_card(request, user, answers, True)
                        return json.jsonify({'cards': [card]})
                else:
                    text = NO_ANSWER
    elif event['type'] == 'CARD_CLICKED':
        # Join team.
        if event['action']['actionMethodName'] == 'join_team':
            team_name = event['action']['parameters'][0]['value']
            if is_room:
                if Database.join_room_to_team(team_name=team_name, space=space):
                    text = f"This room has joined the team '{team_name}'."
                else:
                    text = f"🤕 Sorry, I couldn't add this room to the team '{team_name}'"
            else:
                if Database.join_team(google_id=user.google_id, team_name=team_name):
                    text = f"You have joined the team '{team_name}'."
                else:
                    text = f"🤕 Sorry, I couldn't add you to the team '{team_name}'"
        if event['action']['actionMethodName'] == 'send_answers':
            if is_room:
                text = f"🤕 Sorry, something went wrong."
            else:
                app.logger.info("Publish to the team room.")
                answers = Database.get_standup_answers(google_id=user.google_id)
                message_id = Database.get_standup_answer_message_id(google_id=user.google_id)
                card = Cards.get_standup_card(request, user, answers, False)
                team = Database.get_team_of_user(google_id=user.google_id)
                app.logger.info(f"Message id: {message_id}")
                if team:
                    if team.space:
                        if message_id:
                            update_standup_card(card, user, team, message_id)
                            text = f"Your standup answers have been updated in your team room."
                        else:
                            send_standup_card(card, user, team)
                            text = f"Your standup answers have been published in your team room."
                    else:
                        text = f"🤕 Sorry, your team room does either not have the standup bot " \
                               f"and/or did not yet join a team. Add the standup bot to your team room " \
                               f"and run `/join_team` in your team room to join a team."
                else:
                    text = f"🤕 Sorry, you did not yet join a team. Use `/join_team` to join a team."
    else:
        return
    return json.jsonify({'text': text})


@app.route('/static/<path:path>')
def static_dir(path):
    return send_from_directory("static", path)


if __name__ == '__main__':
    setup_logger(True, '')
    Database.update()
    app.run(host='0.0.0.0', port=5000)
