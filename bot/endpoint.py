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
        return AddedToSpace.handle_event(user, is_room)

    elif event['type'] == 'REMOVED_FROM_SPACE':
        return RemovedFromSpace.handle_event(user, space, is_room)

    elif event['type'] == 'MESSAGE':
        return Message.handle_event(event, user, space, is_room)

    elif event['type'] == 'CARD_CLICKED':
        return CardClicked.handle_event(event, user, space, is_room)

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
