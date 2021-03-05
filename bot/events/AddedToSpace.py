from flask import json
from typing import Any

import bot.utils.Cards as Cards
import bot.utils.User as User
import bot.utils.storage.Storage as Storage


def add(user: User, is_room: bool) -> Any:
    if not is_room:
        Storage.add_user(user=user)
    teams = Storage.get_teams()
    return json.jsonify(Cards.get_team_selection_card(teams, is_room, True))
