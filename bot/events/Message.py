from flask import json
from typing import Any

import bot.utils.Cards as Cards
import bot.utils.User as User
import bot.utils.storage.Storage as Storage
from bot.utils.Logger import logger
from bot.utils.Weekdays import Weekdays

NO_ANSWER = "🤔 Sorry, I don't have an answer for that."


def add_team(event) -> Any:
    team_name = ''
    if 'argumentText' in event['message']:
        team_name = event['message']['argumentText'].strip(' "\'')
    if team_name and Storage.add_team(team_name=team_name):
        text = f"I successfully added the new team '{team_name}'."
    else:
        text = f"🤕 Sorry, I couldn't add the new team '{team_name}'."
    return json.jsonify({'text': text})


def get_teams() -> Any:
    teams = Storage.get_teams()
    return json.jsonify(Cards.get_team_list_card(teams))


def join_team(is_room: bool) -> Any:
    teams = Storage.get_teams()
    return json.jsonify(Cards.get_team_selection_card(teams, is_room, False))


def get_users(event) -> Any:
    team_name = ''
    if 'argumentText' in event['message']:
        team_name = event['message']['argumentText'].strip(' "\'')
    users = Storage.get_users(team_name=team_name)
    return json.jsonify(Cards.get_user_list_card(users))


def trigger_standup(user: User, is_room: bool) -> Any:
    if is_room:
        text = "🤕 Sorry, but this command has no effect in a room."
    else:
        Storage.reset_standup(google_id=user.google_id)
        next_question = Storage.get_current_question(google_id=user.google_id)
        if next_question is None:
            text = "🤕 Sorry, I could not find a standup question. " \
                   "Add new questions with `/add_question QUESTION`."
        else:
            text = f"*Hi {user.name}!*\nYou requested to do the standup.\n\n" \
                   f"_{next_question.question}_"
    return json.jsonify({'text': text})


def enable_schedule(user: User, is_room: bool) -> Any:
    if is_room:
        text = "🤕 Sorry, but this command has no effect in a room."
        return json.jsonify({'text': text})
    else:
        schedules = Storage.get_schedules(google_id=user.google_id)
        return json.jsonify(Cards.get_schedule_enable_card(schedules, False))


def change_schedule_time(event, user: User, is_room: bool) -> Any:
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
                and Storage.update_schedule_time(google_id=user.google_id, day=schedule_day,
                                                 time=schedule_time):
            text = f"Your standup schedule time for '{schedule_day}' is now '{schedule_time}'."
        else:
            text = f"🤕 Sorry, I couldn't change your standup schedule time '{schedule_time}' " \
                   f"for '{schedule_day}'. Use e.g. `/change_schedule_time monday 09:00:00`"
    return json.jsonify({'text': text})


def get_schedules(user: User, is_room: bool) -> Any:
    if is_room:
        text = "🤕 Sorry, but this command has no effect in a room."
        return json.jsonify({'text': text})
    else:
        schedules = Storage.get_schedules(google_id=user.google_id)
        return json.jsonify(Cards.get_schedule_list_card(schedules))


def leave_team(user: User, space: str, is_room: bool) -> Any:
    if is_room:
        Storage.leave_team_with_room(space=space)
        text = "The room is no longer part of a team. Run `/join_team` to join the room to another team."
    else:
        Storage.leave_team(google_id=user.google_id)
        text = "You left the team. Run `/join_team` to join another team."
    return json.jsonify({'text': text})


def remove_team() -> Any:
    teams = Storage.get_teams()
    return json.jsonify(Cards.get_team_remove_card(teams, False))


def get_questions(user: User) -> Any:
    questions = Storage.get_questions(google_id=user.google_id)
    if questions:
        return json.jsonify(Cards.get_question_list_card(questions))
    else:
        text = "🤕 Sorry, I couldn't find any questions for you. " \
               "Make sure you joined a team with `/join_team` and/or your team as questions. " \
               "Use `/add_question QUESTION` to add a new question for your team."
        json.jsonify({'text': text})


def add_question(event, user: User) -> Any:
    question = ''
    if 'argumentText' in event['message']:
        question = event['message']['argumentText'].strip(' "\'')
    if question and Storage.add_question(google_id=user.google_id, question=question):
        text = f"I successfully added the new question '{question}'."
    else:
        text = f"🤕 Sorry, I couldn't add the new question '{question}'. " \
               f"Make sure you joined a team with `/join_team`."
    return json.jsonify({'text': text})


def remove_question(user: User) -> Any:
    questions = Storage.get_questions(google_id=user.google_id)
    return json.jsonify(Cards.get_question_remove_card(questions, False))


def reorder_questions(user) -> Any:
    questions = Storage.get_questions(google_id=user.google_id)
    if questions:
        return json.jsonify(Cards.get_question_reorder_card(questions, 1))
    else:
        text = "🤕 Sorry, I couldn't find any questions of your team."
        return json.jsonify({'text': text})


def generic_input(event, user: User, is_room) -> Any:
    text = ''
    if is_room:
        text = NO_ANSWER
    else:
        previous_question = Storage.get_previous_question(google_id=user.google_id)
        logger.debug(f"Previous question: {previous_question.id_}, {previous_question.question}, "
                     f"{previous_question.order}")
        if previous_question:
            current_question = Storage.get_current_question(google_id=user.google_id,
                                                            previous_question=previous_question)
            logger.debug(f"Current question: {current_question.id_}, {current_question.question}, "
                         f"{current_question.order}")
            if current_question:
                answer = event['message']['text']
                Storage.add_standup_answer(google_id=user.google_id, answer=answer,
                                           current_question=current_question)
                next_question = Storage.get_current_question(google_id=user.google_id,
                                                             previous_question=current_question)
                logger.debug(f"Next question: {next_question}")
                if next_question is None:
                    answers = Storage.get_standup_answers(google_id=user.google_id)
                    card = Cards.get_standup_card(user, answers, True)
                    return json.jsonify({'cards': [card]})
                else:
                    text = f"_{next_question.question}_"
        else:
            text = NO_ANSWER
    return json.jsonify({'text': text})
