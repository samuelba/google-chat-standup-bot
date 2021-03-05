import os
import psycopg2
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Optional, Sequence, Tuple

import bot.utils.storage.Database as Database
from bot.utils.Logger import logger
from bot.utils.Question import Question
from bot.utils.Schedule import Schedule
from bot.utils.Team import Team
from bot.utils.User import User


def get_password():
    try:
        return Path(os.getenv('DB_PASSWORD_FILE', '')).read_text()
    except Exception:
        return os.getenv('DB_PASSWORD', '')


CONN_INFO = {
    'host': os.getenv('DB_HOST', ''),
    'port': os.getenv('DB_PORT', ''),
    'user': os.getenv('DB_USERNAME', ''),
    'password': get_password(),
    'dbname': os.getenv('DB_NAME', '')
}


def connect(conn_info):
    connection = psycopg2.connect(**conn_info)
    return connection


@contextmanager
def transaction(name="transaction", **kwargs):
    def rollback(conn):
        if conn:
            conn.rollback()

    connection = None
    try:
        connection = connect(CONN_INFO)
        yield connection
        connection.commit()
    except psycopg2.OperationalError as e:
        logger.error(f"{name}: Operational database error: {e}")
        rollback(connection)
    except psycopg2.DatabaseError as e:
        logger.error(f"{name}: Database error: {e}")
        rollback(connection)
    except Exception as e:
        logger.error(f"{name}: Exception: {e}")
        rollback(connection)
    finally:
        if connection:
            connection.close()


def transact(func):
    """
    Creates a connection per-transaction, committing when complete or rolling back if there is an exception.
    It also ensures that the conn is closed when we're done.
    """
    @wraps(func)
    def inner(*args, **kwargs):
        with transaction(name=func.__name__) as connection:
            return func(connection, *args, **kwargs)
    return inner


@transact
def add_user(connection, user: User) -> bool:
    return Database.add_user(connection, user)


@transact
def disable_user(connection, user: User) -> bool:
    return Database.disable_user(connection, user)


@transact
def add_team(connection, team_name: str) -> bool:
    return Database.add_team(connection, team_name)


@transact
def get_teams(connection) -> Sequence[Team]:
    return Database.get_teams(connection)


@transact
def join_team(connection, google_id: str, team_name: str) -> bool:
    return Database.join_team(connection, google_id, team_name)


@transact
def leave_team(connection, google_id: str) -> bool:
    return Database.leave_team(connection, google_id)


@transact
def remove_team(connection, team_name: str) -> bool:
    return Database.remove_team(connection, team_name)


@transact
def join_room_to_team(connection, team_name: str, space: str) -> bool:
    return Database.join_room_to_team(connection, team_name, space)


@transact
def leave_team_with_room(connection, space: str) -> bool:
    return Database.leave_team_with_room(connection, space)


@transact
def get_team_of_user(connection, google_id: str) -> Optional[Team]:
    return Database.get_team_of_user(connection, google_id)


@transact
def get_users(connection, team_name: str = '') -> Sequence[User]:
    return Database.get_users(connection, team_name)


@transact
def get_questions(connection, google_id: str) -> Sequence[Question]:
    return Database.get_questions(connection, google_id)


@transact
def add_question(connection, google_id: str, question: str) -> bool:
    return Database.add_question(connection, google_id, question)


@transact
def remove_question(connection, question_id: int) -> bool:
    return Database.remove_question(connection, question_id)


@transact
def reorder_questions(connection, team_id: int, question_id: int, order_step: int) -> bool:
    return Database.reorder_questions(connection, team_id, question_id, order_step)


@transact
def get_previous_question(connection, google_id: str) -> Optional[Question]:
    return Database.get_previous_question(connection, google_id)


@transact
def get_current_question(connection, google_id: str, previous_question: Question = None) -> Optional[Question]:
    return Database.get_current_question(connection, google_id, previous_question)


@transact
def reset_standup(connection, google_id: str) -> bool:
    return Database.reset_standup(connection, google_id)


@transact
def add_standup_answer(connection, google_id: str, answer: str, current_question: Question = None) -> bool:
    return Database.add_standup_answer(connection, google_id, answer, current_question)


@transact
def get_standup_answers(connection, google_id: str) -> Sequence[Tuple]:
    return Database.get_standup_answers(connection, google_id)


@transact
def get_standup_answer_message_id(connection, google_id: str) -> str:
    return Database.get_standup_answer_message_id(connection, google_id)


@transact
def set_message_id(connection, google_id: str, message_id: str) -> bool:
    return Database.set_message_id(connection, google_id, message_id)


@transact
def get_users_with_schedule(connection, day: str, time: str) -> Sequence[User]:
    return Database.get_users_with_schedule(connection, day, time)


@transact
def enable_schedule(connection, google_id: str, day: str, enable: bool) -> bool:
    return Database.enable_schedule(connection, google_id, day, enable)


@transact
def update_schedule_time(connection, google_id: str, day: str, time: str) -> bool:
    return Database.update_schedule_time(connection, google_id, day, time)


@transact
def get_schedules(connection, google_id: str) -> Sequence[Schedule]:
    return Database.get_schedules(connection, google_id)


@transact
def update(connection) -> bool:
    return Database.update(connection)
