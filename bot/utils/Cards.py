from datetime import date
from typing import Sequence

from bot.utils.Question import Question
from bot.utils.Schedule import Schedule
from bot.utils.Team import Team
from bot.utils.User import User


def get_team_list_card(teams: Sequence[Team]):
    widgets = []
    if not teams:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": "No teams found.",
            }
        })
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


def get_team_remove_card(teams: Sequence[Team], is_update: bool):
    widgets = []
    if not teams:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": "No teams found.",
            }
        })
    for team in teams:
        if team.space:
            widgets.append({
                "keyValue": {
                    "contentMultiline": "true",
                    "content": f"{team.name}",
                    "bottomLabel": "Room is assigned."
                }
            })
        else:
            widgets.append({
                "keyValue": {
                    "contentMultiline": "true",
                    "content": f"{team.name}",
                    "bottomLabel": "No room is assigned.",
                    "button": {
                        "textButton": {
                            "text": "REMOVE",
                            "onClick": {
                                "action": {
                                    "actionMethodName": "remove_team",
                                    "parameters": [{"key": "team_name", "value": team.name}]
                                }
                            }
                        }
                    }
                }
            })
    result = \
        {"cards": [{
            "header": {"title": "Teams"},
            "sections": [{"widgets": widgets}]
        }]}
    if is_update:
        result['actionResponse'] = {"type": "UPDATE_MESSAGE"}
    return result


def get_team_selection_card(teams: Sequence[Team], is_room: bool, with_greeting: bool = False):
    title = "Thanks for adding me!" if with_greeting else \
        ("You requested to join with this room a new team" if is_room else "You requested to join a new team")
    subtitle = "Select a team for this room" if is_room else "Select your team"
    widgets = []
    content = ''
    # Check if some teams exists.
    if not teams:
        content = "No teams found."
    # If a room requested the join team card, check if unassigned teams are available.
    if is_room:
        has_free_team = False
        for team in teams:
            if not team.space:
                has_free_team = True
                break
        if not has_free_team:
            content = "No unassigned teams found."
    # Either no teams exist, or no more unassigned teams.
    if content:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": f"{content}"
            }
        })
    else:
        for team in teams:
            if is_room and team.space:
                continue
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


def get_standup_card(user: User, answers: Sequence, with_confirmation: bool):
    today = date.today()
    today_str = today.strftime("%b %d %Y")
    sections = []
    for answer in answers:
        sections.append(
            {"widgets": [
                {"keyValue": {
                    "topLabel": answer[0],
                    "contentMultiline": "true",
                    "content": f"{answer[1]}"
                }}
            ]}
        )

    card = {
        "header": {"title": f"{user.name}",
                   "subtitle": f"{today_str}",
                   "imageUrl": f"{user.avatar_url}"},
        "sections": sections
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
                "content": "No schedules found.",
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


def get_schedule_enable_card(schedules: Sequence[Schedule], is_update: bool):
    widgets = []
    if not schedules:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": "No schedules found.",
            }
        })
    for schedule in schedules:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": f"{schedule.day}, {schedule.time}",
                "bottomLabel": f"{'enabled' if schedule.enabled else 'disabled'}",
                "button": {
                    "textButton": {
                        "text": "ENABLE" if not schedule.enabled else "DISABLE",
                        "onClick": {
                            "action": {
                                "actionMethodName": "enable_schedule",
                                "parameters": [{"key": "day", "value": schedule.day},
                                               {"key": "enable", "value": "True" if not schedule.enabled else "False"}]
                            }
                        }
                    }
                }
            }
        })
    result = \
        {"cards": [{
            "header": {"title": "Schedules"},
            "sections": [{"widgets": widgets}]
        }]}
    if is_update:
        result['actionResponse'] = {"type": "UPDATE_MESSAGE"}
    return result


def get_user_list_card(users: Sequence[User]):
    widgets = []
    if not users:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": "No users found.",
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


def get_question_list_card(questions: Sequence[Question]):
    widgets = []
    if not questions:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": "No questions found.",
            }
        })
    for question in questions:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": f"{question.question}",
                "bottomLabel": f"Order: {question.order}"
            }
        })
    return {"cards": [{
                "header": {"title": "Questions"},
                "sections": [{"widgets": widgets}]
            }]}


def get_question_remove_card(questions: Sequence[Question], is_update: bool):
    widgets = []
    if not questions:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": "No questions found.",
            }
        })
    for question in questions:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": f"{question.question}",
                "bottomLabel": f"Order: {question.order}",
                "button": {
                    "textButton": {
                        "text": "REMOVE",
                        "onClick": {
                            "action": {
                                "actionMethodName": "remove_question",
                                "parameters": [{"key": "question_id", "value": question.id_},
                                               {"key": "question", "value": question.question}]
                            }
                        }
                    }
                }
            }
        })
    result = \
        {"cards": [{
            "header": {"title": "Questions"},
            "sections": [{"widgets": widgets}]
        }]}
    if is_update:
        result['actionResponse'] = {"type": "UPDATE_MESSAGE"}
    return result


def get_question_reorder_card(questions: Sequence[Question], order_step: int):
    widgets = []
    if not questions:
        widgets.append({
            "keyValue": {
                "contentMultiline": "true",
                "content": "No questions found.",
            }
        })
    for question in questions:
        if question.order >= order_step:
            widgets.append({
                "keyValue": {
                    "contentMultiline": "true",
                    "content": f"{question.question}",
                    "bottomLabel": f"Order: {question.order}",
                    "button": {
                        "textButton": {
                            "text": "SELECT",
                            "onClick": {
                                "action": {
                                    "actionMethodName": "reorder_questions",
                                    "parameters": [{"key": "question_id", "value": question.id_},
                                                   {"key": "question", "value": question.question},
                                                   {"key": "order_step", "value": order_step},
                                                   {"key": "team_id", "value": question.team_id}]
                                }
                            }
                        }
                    }
                }
            })
        else:
            widgets.append({
                "keyValue": {
                    "contentMultiline": "true",
                    "content": f"{question.question}",
                    "bottomLabel": f"Order: {question.order}"
                }
            })
    result = \
        {"cards": [{
            "header": {"title": "Questions", "subtitle": "Select the questions in the order you want them."},
            "sections": [{"widgets": widgets}]
        }]}
    if order_step > 1:
        result['actionResponse'] = {"type": "UPDATE_MESSAGE"}
    return result
