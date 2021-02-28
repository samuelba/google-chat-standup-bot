from datetime import date
from typing import Dict, Sequence

import bot.utils.Questions as Questions
from bot.utils.Schedule import Schedule
from bot.utils.Team import Team
from bot.utils.User import User


def get_team_list_card(teams: Sequence[Team]):
    widgets = []
    if not teams:
        teams.append(Team(name="No teams found.", space=''))
    for team in teams:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": f"{team.name}",
                "bottomLabel": f"{'Room is assigned.' if team.space else 'No room is assigned.'}"
            }
        })
    return {"cards": [{
                "header": {"title": "Teams"},
                "sections": [{"widgets": widgets}]
            }]}


def get_team_selection_card(teams: Sequence[Team], with_greeting: bool = False):
    title = "Thanks for adding me!" if with_greeting else "You requested to join a new team"
    subtitle = "Select your team"
    widgets = []
    for team in teams:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": f"{team.name}",
                "button": {
                    "textButton": {
                        "text": "JOIN",
                        "onClick": {
                            "action": {
                                "actionMethodName": "join_team",
                                "parameters": [{"key": "team", "value": team.name}]
                            }
                        }
                    }
                }
            }
        })

    return {"cards": [{
                "header": {"title": title, "subtitle": subtitle},
                "sections": [{"widgets": widgets}]
            }]}


def get_standup_card(request, user: User, answers: Dict, with_confirmation: bool):
    today = date.today()
    today_str = today.strftime("%b %d %Y")
    icon_done_url = f"https://{request.host}/static/images/done.png"
    icon_list_url = f"https://{request.host}/static/images/list.png"
    icon_blocking_url = f"https://{request.host}/static/images/blocking.png"
    card = {
        "header": {"title": f"{user.name}",
                   "subtitle": f"{today_str}",
                   "imageUrl": f"{user.avatar_url}"},
        "sections": [
            {"widgets": [
                {"keyValue": {
                    "iconUrl": icon_done_url,
                    "topLabel": Questions.QUESTION_RETROSPECT,
                    "contentMultiline": "true",
                    "content": f"{answers['1_retrospect']}"
                }}
            ]},
            {"widgets": [
                {"keyValue": {
                    "iconUrl": icon_list_url,
                    "topLabel": Questions.QUESTION_OUTLOOK,
                    "contentMultiline": "true",
                    "content": f"{answers['2_outlook']}"
                }}
            ]},
            {"widgets": [
                {"keyValue": {
                    "iconUrl": icon_blocking_url,
                    "topLabel": Questions.QUESTION_BLOCKING,
                    "contentMultiline": "true",
                    "content": f"{answers['3_blocking']}"
                }}
            ]}
        ]
    }
    if with_confirmation:
        confirmation = {
            "widgets": [{
                "keyValue": {
                    "contentMultiline": "true",
                    "content": "<b>Thank you for your time.</b><br><br>"
                               "Send the answers to your team group chat or redo them by invoking: "
                               "<b><font color=\"#ff0000\">/standup</font></b>",
                    "button": {
                        "textButton": {
                            "text": "SEND",
                            "onClick": {
                                "action": {
                                    "actionMethodName": "send_answers"
                                }
                            }
                        }
                    }
                }
            }]
        }
        card['sections'].append(confirmation)
    return card


def get_schedule_list_card(schedules: Sequence[Schedule]):
    widgets = []
    if not schedules:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": f"No schedules found.",
            }
        })
    for schedule in schedules:
        widgets.append({
            "keyValue": {
                "content": f"{schedule.day}, {schedule.time}",
                "bottomLabel": f"{'enabled' if schedule.enabled else 'disabled'}"
            }
        })
    return {"cards": [{
                "header": {"title": "Schedules"},
                "sections": [{"widgets": widgets}]
            }]}


def get_user_list_card(users: Sequence[User]):
    widgets = []
    if not users:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": f"No users found.",
            }
        })
    for user in users:
        widgets.append({
            "keyValue": {
                "iconUrl": user.avatar_url,
                "topLabel": f"{'ACTIVE' if user.active else 'INACTIVE'}",
                "content": f"{user.name}, {user.email}",
                "bottomLabel": f"{user.team_name}"
            }
        })
    return {"cards": [{
                "header": {"title": "Users"},
                "sections": [{"widgets": widgets}]
            }]}
