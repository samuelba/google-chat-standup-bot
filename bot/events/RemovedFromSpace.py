from flask import json
from typing import Any

import bot.utils.User as User
import bot.utils.storage.Storage as Storage


def handle_event(user: User, space: bool, is_room: str) -> Any:
    if is_room:
        Storage.leave_team_with_room(space=space)
    else:
        Storage.disable_user(user=user)
    return json.jsonify({'text': ''})
