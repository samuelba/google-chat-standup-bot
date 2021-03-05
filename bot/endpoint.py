#!/usr/bin/env python3

import os

from flask import Flask, request, json, Response, send_from_directory
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

import bot.events.AddedToSpace as AddedToSpace
import bot.events.RemovedFromSpace as RemovedFromSpace
import bot.events.CardClicked as CardClicked
import bot.events.Message as Message
import bot.utils.storage.Storage as Storage
from bot.utils.Logger import setup_logger
from bot.utils.User import User

app = Flask(__name__, static_url_path='')

CHAT_ISSUER = 'chat@system.gserviceaccount.com'
PUBLIC_CERT_URL_PREFIX = 'https://www.googleapis.com/service_accounts/v1/metadata/x509/'
AUDIENCE = os.environ.get('AUDIENCE', '')


def get_user_from_event(event) -> User:
    google_id = event['user']['name']
    display_name = event['user']['displayName']
    email = event['user']['email']
    avatar_url = event['user']['avatarUrl']
    space = event['space']['name']
    return User(0, google_id, display_name, email, avatar_url, space, False, '')


def is_authentication_ok() -> bool:
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
            return False
    except ValueError:
        app.logger.error("Invalid credentials.")
        return False
    return True


@app.route('/api/v1/', methods=['POST'])
def on_event():
    """
    Handles an event from Google Chat.
    """

    # Check the authorization.
    if not is_authentication_ok():
        return Response("Unauthorized.", status=401)

    # Handle the request.
    event = request.get_json()
    text = ''
    user = get_user_from_event(event)
    is_room = event['space']['type'] == 'ROOM'
    space = event['space']['name']

    app.logger.info(f"The event: {event}")
    if event['type'] == 'ADDED_TO_SPACE':
        return AddedToSpace.add(user, is_room)

    elif event['type'] == 'REMOVED_FROM_SPACE':
        return RemovedFromSpace.remove(user, space, is_room)

    elif event['type'] == 'MESSAGE':
        if 'slashCommand' in event['message']:
            command = event['message']['slashCommand']['commandId']
            app.logger.debug(f"Slash command {command}")
            # /add_team team_name
            if command == '1':
                return Message.add_team(event)
            # /teams
            if command == '3':
                return Message.get_teams()
            # /join_team
            if command == '4':
                return Message.join_team(is_room)
            # /users [team_name]
            if command == '5':
                return Message.get_users(event)
            # /standup
            if command == '6':
                return Message.trigger_standup(user, is_room)
            # /enable_schedule or /disable_schedule
            if command == '7' or command == '8':
                return Message.enable_schedule(user, is_room)
            # /change_schedule_time day time
            if command == '9':
                return Message.change_schedule_time(event, user, is_room)
            # /schedules
            if command == '10':
                return Message.get_schedules(user, is_room)
            # /leave_team
            if command == '11':
                return Message.leave_team(user, space, is_room)
            # /remove_team
            if command == '12':
                return Message.remove_team()
            # /questions
            if command == '13':
                return Message.get_questions(user)
            # /add_question QUESTION
            if command == '14':
                return Message.add_question(event, user)
            # /remove_question
            if command == '15':
                return Message.remove_question(user)
            # /reorder_questions
            if command == '16':
                return Message.reorder_questions(user)

        # Handle standup answers and generic requests.
        else:
            return Message.generic_input(event, user, is_room)
    elif event['type'] == 'CARD_CLICKED':
        # Join team.
        if event['action']['actionMethodName'] == 'join_team':
            return CardClicked.join_team(event, user, space, is_room)
        # Remove team.
        if event['action']['actionMethodName'] == 'remove_team':
            return CardClicked.remove_team(event)
        # Send the standup answers to the team room.
        if event['action']['actionMethodName'] == 'send_answers':
            return CardClicked.send_standup_answers_to_room(user, is_room)
        # Enable/disable schedule.
        if event['action']['actionMethodName'] == 'enable_schedule':
            return CardClicked.enable_schedule(event, user)
        # Remove question.
        if event['action']['actionMethodName'] == 'remove_question':
            return CardClicked.remove_question(event, user)
        # Reorder questions.
        if event['action']['actionMethodName'] == 'reorder_questions':
            return CardClicked.reorder_questions(event, user)

    else:
        text = "Sorry, I don't know what to say."
    return json.jsonify({'text': text})


@app.route('/static/<path:path>')
def static_dir(path):
    return send_from_directory("static", path)


if __name__ == '__main__':
    setup_logger(True, '')
    Storage.update()
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
    # app.run(host='0.0.0.0', port=5000, debug=True)
