#!/usr/bin/env python3

import os
import sys

from flask import Flask, request, json, Response, send_from_directory
from google.oauth2 import id_token
from google.auth.transport import requests
from httplib2 import Http

import bot.utils.Cards as Cards
import bot.utils.Database as Database
import bot.utils.Questions as Questions
import bot.utils.Schedule as Schedule
from bot.utils.Logger import setup_logger
from bot.utils.User import User
from bot.utils.Weekdays import Weekdays

app = Flask(__name__, static_url_path='')

CHAT_ISSUER = 'chat@system.gserviceaccount.com'
PUBLIC_CERT_URL_PREFIX = 'https://www.googleapis.com/service_accounts/v1/metadata/x509/'
AUDIENCE = os.environ.get('AUDIENCE', '')


def send_standup_card(card, webhook: str):
    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
    http_obj = Http()
    response = http_obj.request(
        uri=webhook,
        method='POST',
        headers=message_headers,
        body=json.dumps(card)
    )
    app.logger.debug(f"Send standup card response: {response}")


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
        id_info = id_token.verify_token(auth_token, requests.Request(), AUDIENCE,
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

    app.logger.info(f"The event: {event}")
    if event['type'] == 'ADDED_TO_SPACE':
        Database.add_user(user=user)
        teams = Database.get_teams()
        return json.jsonify(Cards.get_team_selection_card(teams, True))

    elif event['type'] == 'REMOVED_FROM_SPACE':
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
            # /set_team_webhook team_name webhook
            if event['message']['slashCommand']['commandId'] == '2':
                argument = ''
                arguments = []
                if 'argumentText' in event['message']:
                    argument = event['message']['argumentText']
                    arguments = argument.rsplit(' ', 1)
                if len(arguments) != 2:
                    text = f"I couldn't extract team name and webhook from '{argument}'. " \
                           f"Call it like this /set_team_webhook \"Team Name\" https://..."
                else:
                    team_name = arguments[0].strip(' "\'')
                    webhook = arguments[1].strip(' "\'')
                    if Database.set_team_webhook(team_name=team_name, webhook=webhook):
                        text = f"I successfully set the webhook '{webhook}' for the team '{team_name}'."
                    else:
                        text = f"🤕 Sorry, I couldn't set the webhook '{webhook}' for the team '{team_name}'."
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
                Database.reset_standup(google_id=user.google_id)
                text = Questions.get_standup_question(user.name, '0_na')
            # /disable_schedule day
            if event['message']['slashCommand']['commandId'] == '7':
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
                schedules = Database.get_schedules(google_id=user.google_id)
                return json.jsonify(Cards.get_schedule_list_card(schedules))

        # Handle standup answers and generic requests.
        else:
            question_type = Database.get_standup_question_type(google_id=user.google_id)
            if question_type and question_type != '3_blocking':
                answer = event['message']['text']
                success, question_type = Database.add_standup_answer(google_id=user.google_id, answer=answer)
                text = Questions.get_standup_question(user.name, question_type)
                if question_type == '3_blocking':
                    app.logger.info("Publish to the team webhook.")
                    answers = Database.get_standup_answers(google_id=user.google_id)
                    return json.jsonify(Cards.get_standup_card(request, user, answers, True))
            else:
                text = "🤔 I don't have an answer for that."
    elif event['type'] == 'CARD_CLICKED':
        # Join team.
        if event['action']['actionMethodName'] == 'join_team':
            team_name = event['action']['parameters'][0]['value']
            if Database.join_team(google_id=user.google_id, team_name=team_name):
                text = f"You have joined the team '{team_name}'."
            else:
                text = f"🤕 Sorry, I couldn't add you to the team '{team_name}'"
        if event['action']['actionMethodName'] == 'send_answers':
            app.logger.info("Publish to the team webhook.")
            answers = Database.get_standup_answers(google_id=user.google_id)
            card = Cards.get_standup_card(request, user, answers, False)
            webhook = Database.get_webhook(google_id=user.google_id)
            if webhook:
                send_standup_card(card, webhook)
                text = f"Your standup answers have been published in your team group chat."
            else:
                text = f"🤕 Sorry, I couldn't find a team webhook or you did not yet join a team."
    else:
        return
    return json.jsonify({'text': text})


@app.route('/static/<path:path>')
def static_dir(path):
    return send_from_directory("static", path)


if __name__ == '__main__':
    setup_logger(True, '')
    Database.update()
    app.run(host='0.0.0.0', port=5000, debug=True)
