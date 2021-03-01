import os
import psycopg2
from functools import wraps
from pathlib import Path
from psycopg2 import OperationalError
from typing import Dict, Sequence, Tuple

from bot.utils.Logger import logger
from bot.utils.Schedule import Schedule
from bot.utils.Team import Team
from bot.utils.User import User
from bot.utils.Weekdays import Weekdays


def get_password():
    try:
        return Path(os.environ.get('DB_PASSWORD_FILE', '')).read_text()
    except Exception as e:
        return os.environ.get('DB_PASSWORD', '')


CONN_INFO = {
    'host': os.environ.get('DB_HOST', ''),
    'port': os.environ.get('DB_PORT', ''),
    'user': os.environ.get('DB_USERNAME', ''),
    'password': get_password(),
    'dbname': os.environ.get('DB_NAME', '')
}
DB_VERSION = 1


def with_connection(conn_info):
    def wrap(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ret = None
            connection = None
            try:
                logger.debug(f"Connect to {conn_info['host']}:{conn_info['port']}. "
                             f"Database: {conn_info['dbname']}/public")
                connection = psycopg2.connect(**conn_info)
                ret = func(connection, *args, **kwargs)
                connection.commit()
            except OperationalError as e:
                logger.error(f"Operational database error: {e}")
            except psycopg2.DatabaseError as e:
                logger.error(f"Database error: {e}")
                connection.rollback()
            finally:
                if connection:
                    connection.close()
            return ret
        return wrapper
    return wrap


@with_connection(CONN_INFO)
def add_user(connection, user: User):
    cursor = connection.cursor()

    logger.info(f"Add/update user: {user}")
    sql = "SELECT * " \
          "FROM users AS u " \
          "INNER JOIN teams AS t ON t.id = u.team_id " \
          "WHERE u.google_id = %s"
    cursor.execute(sql, (user.google_id,))
    ret = cursor.fetchall()
    if ret:
        logger.info(f"Update user: {user}")
        sql = "UPDATE users " \
              "SET name = %s, email = %s, avatar_url = %s, space = %s, active = %s " \
              "WHERE google_id = %s"
        cursor.execute(sql, (user.name, user.email, user.avatar_url, user.space, True, user.google_id))
    else:
        logger.info(f"Add new user: {user}")
        sql = "INSERT INTO users (google_id, name, email, avatar_url, space, active) " \
              "VALUES (%s, %s, %s, %s, %s, %s) " \
              "RETURNING id"
        cursor.execute(sql, (user.google_id, user.name, user.email, user.avatar_url, user.space, True))
        ret = cursor.fetchone()
        user_id, = ret
        time = '09:00:00'
        sql = "INSERT INTO schedules AS s (user_id, day, time, enabled) " \
              "VALUES (%s, %s, %s, True), " \
              "       (%s, %s, %s, True), " \
              "       (%s, %s, %s, True), " \
              "       (%s, %s, %s, True), " \
              "       (%s, %s, %s, True), " \
              "       (%s, %s, %s, False), " \
              "       (%s, %s, %s, False)"
        values = ()
        for day in Weekdays:
            values += (user_id, day, time)
        cursor.execute(sql, values)


@with_connection(CONN_INFO)
def disable_user(connection, user: User):
    cursor = connection.cursor()

    logger.info(f"Disable user: {user}")
    sql = "SELECT * " \
          "FROM users AS u " \
          "INNER JOIN teams AS t ON t.id = u.team_id " \
          "WHERE u.google_id = %s"
    cursor.execute(sql, (user.google_id,))
    ret = cursor.fetchall()
    if ret:
        sql = "UPDATE users " \
              "SET active = %s " \
              "WHERE google_id = %s"
        cursor.execute(sql, (False, user.google_id))


@with_connection(CONN_INFO)
def add_team(connection, team_name: str) -> bool:
    cursor = connection.cursor()

    sql = "SELECT * " \
          "FROM teams " \
          "WHERE name = %s"
    cursor.execute(sql, (team_name,))
    ret = cursor.fetchall()
    if ret:
        return False
    else:
        sql = "INSERT INTO teams (name) " \
              "VALUES (%s)"
        cursor.execute(sql, (team_name,))
    return True


@with_connection(CONN_INFO)
def get_teams(connection) -> Sequence[Team]:
    cursor = connection.cursor()
    sql = "SELECT name, space " \
          "FROM teams " \
          "ORDER BY name ASC"
    cursor.execute(sql)
    ret = cursor.fetchall()
    return [Team(name, space) for name, space in ret]


@with_connection(CONN_INFO)
def join_team(connection, google_id: str, team_name: str) -> bool:
    cursor = connection.cursor()
    sql = "SELECT id " \
          "FROM teams " \
          "WHERE name = %s"
    cursor.execute(sql, (team_name,))
    ret = cursor.fetchone()
    if not ret:
        return False
    team_id, = ret
    sql = "UPDATE users " \
          "SET team_id = %s " \
          "WHERE google_id = %s " \
          "RETURNING id"
    cursor.execute(sql, (team_id, google_id))
    ret = cursor.fetchone()
    return ret is not None


@with_connection(CONN_INFO)
def leave_team(connection, google_id: str) -> bool:
    cursor = connection.cursor()
    sql = "UPDATE users " \
          "SET team_id = NULL " \
          "WHERE google_id = %s " \
          "RETURNING id"
    cursor.execute(sql, (google_id,))
    ret = cursor.fetchone()
    return ret is not None


@with_connection(CONN_INFO)
def remove_team(connection, team_name: str) -> bool:
    cursor = connection.cursor()
    # Check if the team as still users.
    sql = "SELECT * " \
          "FROM users as u " \
          "INNER JOIN teams as t ON t.id = u.team_id AND t.name = %s"
    cursor.execute(sql, (team_name,))
    ret = cursor.fetchall()
    if ret:
        return False

    # Delete the team if it has no space assigned.
    sql = "DELETE FROM teams " \
          "WHERE name = %s AND space IS NULL " \
          "RETURNING id"
    cursor.execute(sql, (team_name,))
    ret = cursor.fetchone()
    return ret is not None


@with_connection(CONN_INFO)
def join_room_to_team(connection, team_name: str, space: str) -> bool:
    cursor = connection.cursor()
    # Check if this team_name as already a space assigned.
    sql = "SELECT space " \
          "FROM teams " \
          "WHERE name = %s"
    cursor.execute(sql, (team_name,))
    ret = cursor.fetchone()
    if ret:
        team_space, = ret
        if team_space:
            return False

    # Remove the space from other teams.
    leave_team_with_room(space=space)

    # Add the space to the team.
    sql = "UPDATE teams " \
          "SET space = %s " \
          "WHERE name = %s " \
          "RETURNING id"
    cursor.execute(sql, (space, team_name))
    ret = cursor.fetchone()
    return ret is not None


@with_connection(CONN_INFO)
def leave_team_with_room(connection, space: str) -> bool:
    cursor = connection.cursor()
    sql = "UPDATE teams " \
          "SET space = NULL " \
          "WHERE space = %s" \
          "RETURNING id"
    cursor.execute(sql, (space,))
    ret = cursor.fetchone()
    return ret is not None


@with_connection(CONN_INFO)
def get_team_of_user(connection, google_id: str) -> Team:
    cursor = connection.cursor()
    sql = "SELECT t.name, t.space " \
          "FROM users AS u " \
          "INNER JOIN teams AS t ON t.id = u.team_id AND u.google_id = %s"
    cursor.execute(sql, (google_id,))
    ret = cursor.fetchone()
    if ret:
        name, space = ret
        return Team(name, space)
    return None


@with_connection(CONN_INFO)
def get_users(connection, team_name) -> Sequence[User]:
    cursor = connection.cursor()
    team_join = "INNER" if team_name else "LEFT"
    team_filter = f"AND t.name = %s" if team_name else ""
    team_filter_value = (team_name,) if team_name else ()
    sql = "SELECT u.id, u.google_id, u.name, u.email, u.avatar_url, u.space, u.active, t.name " \
          "FROM users AS u " \
          f"{team_join} JOIN teams AS t ON t.id = u.team_id {team_filter} " \
          "ORDER BY u.name ASC"
    cursor.execute(sql, team_filter_value)
    ret = cursor.fetchall()
    return [User(id_, google_id, name, email, avatar_url, space, active, team_name)
            for id_, google_id, name, email, avatar_url, space, active, team_name in ret]


@with_connection(CONN_INFO)
def get_standup_question_type(connection, google_id: str) -> str:
    cursor = connection.cursor()
    sql = "SELECT s.question_type " \
          "FROM standups AS s " \
          "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s " \
          "WHERE s.added::date = NOW()::date " \
          "ORDER BY s.added DESC " \
          "LIMIT 1"
    cursor.execute(sql, (google_id,))
    ret = cursor.fetchone()
    if not ret:
        return ''
    current_question_type, = ret
    return current_question_type


@with_connection(CONN_INFO)
def reset_standup(connection, google_id: str):
    cursor = connection.cursor()
    sql = "INSERT INTO standups (user_id, question_type, added) " \
          "SELECT u.id, '0_na', NOW() " \
          "FROM users AS u " \
          "WHERE u.google_id = %s"
    cursor.execute(sql, (google_id,))


@with_connection(CONN_INFO)
def add_standup_answer(connection, google_id: str, answer: str) -> Tuple[bool, str]:
    cursor = connection.cursor()
    sql = "SELECT s.question_type " \
          "FROM standups AS s " \
          "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s " \
          "WHERE s.added::date = NOW()::date " \
          "ORDER BY s.added DESC " \
          "LIMIT 1"
    cursor.execute(sql, (google_id,))
    ret = cursor.fetchone()
    question_type = '0_na'
    if ret:
        current_question_type, = ret
        if current_question_type == '0_na':
            question_type = '1_retrospect'
        if current_question_type == '1_retrospect':
            question_type = '2_outlook'
        if current_question_type == '2_outlook':
            question_type = '3_blocking'

    sql = "INSERT INTO standups (user_id, question_type, answer, added) " \
          "SELECT u.id, %s, %s, NOW() " \
          "FROM users AS u " \
          "WHERE u.google_id = %s " \
          "RETURNING standups.id"
    cursor.execute(sql, (question_type, answer, google_id))
    ret = cursor.fetchone()
    return ret is not None, question_type


@with_connection(CONN_INFO)
def get_standup_answers(connection, google_id: str) -> Dict:
    cursor = connection.cursor()
    sql = "SELECT DISTINCT ON(s.question_type) s.question_type, s.answer " \
          "FROM standups AS s " \
          "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s " \
          "WHERE s.added::date = NOW()::date " \
          "  AND s.question_type != '0_na' " \
          "ORDER BY s.question_type ASC, s.added DESC"
    cursor.execute(sql, (google_id,))
    ret = cursor.fetchall()
    if not ret:
        return dict()
    return {question_type: answer for question_type, answer in ret}


@with_connection(CONN_INFO)
def get_standup_answer_message_id(connection, google_id: str) -> str:
    cursor = connection.cursor()
    sql = "SELECT s.message_id " \
          "FROM standups AS s " \
          "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s " \
          "WHERE s.added::date = NOW()::date " \
          "  AND s.question_type = '3_blocking' AND s.message_id IS NOT NULL"
    cursor.execute(sql, (google_id,))
    ret = cursor.fetchone()
    if not ret:
        return ''
    message_id, = ret
    return message_id


@with_connection(CONN_INFO)
def set_message_id(connection, google_id: str, message_id) -> bool:
    cursor = connection.cursor()
    sql = "UPDATE standups AS s " \
          "SET message_id = %s " \
          "FROM users AS u " \
          "WHERE s.user_id = u.id " \
          "      AND u.google_id = %s " \
          "      AND s.added::date = NOW()::date " \
          "      AND s.question_type = '3_blocking' " \
          "RETURNING s.id"
    cursor.execute(sql, (message_id, google_id))
    ret = cursor.fetchone()
    return ret is not None


@with_connection(CONN_INFO)
def get_users_with_schedule(connection, day: str, time: str) -> Sequence[Tuple[str, str, str]]:
    cursor = connection.cursor()
    sql = "SELECT DISTINCT ON(u.google_id) u.name, u.google_id, u.space, st.question_type " \
          "FROM users AS u " \
          "INNER JOIN schedules AS sch ON u.id = sch.user_id " \
          "           AND sch.day = %s AND sch.enabled AND sch.time <= %s " \
          "LEFT JOIN standups AS st ON st.user_id = u.id AND st.added::date = NOW()::date " \
          "WHERE u.active " \
          "ORDER BY u.google_id, st.added DESC"
    cursor.execute(sql, (day, time))
    ret = cursor.fetchall()
    if not ret:
        return []
    return [(name, google_id, space) for name, google_id, space, question_type in ret if question_type is None]


@with_connection(CONN_INFO)
def enable_schedule(connection, google_id: str, day: str, enable: bool) -> bool:
    cursor = connection.cursor()
    sql = "UPDATE schedules AS s " \
          "SET enabled = %s " \
          "FROM users AS u " \
          "WHERE s.user_id = u.id AND u.google_id = %s AND s.day = %s " \
          "RETURNING s.id"
    cursor.execute(sql, (enable, google_id, day))
    ret = cursor.fetchone()
    return ret is not None


@with_connection(CONN_INFO)
def update_schedule_time(connection, google_id: str, day: str, time: str) -> bool:
    cursor = connection.cursor()
    sql = "UPDATE schedules AS s " \
          "SET time = %s " \
          "FROM users AS u " \
          "WHERE s.user_id = u.id AND u.google_id = %s AND s.day = %s " \
          "RETURNING s.id"
    cursor.execute(sql, (time, google_id, day))
    ret = cursor.fetchone()
    return ret is not None


@with_connection(CONN_INFO)
def get_schedules(connection, google_id: str) -> Sequence[Schedule]:
    cursor = connection.cursor()
    sql = "SELECT s.day, s.time, s.enabled " \
          "FROM schedules AS s " \
          "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s"
    cursor.execute(sql, (google_id,))
    ret = cursor.fetchall()
    return [Schedule(day, time, enabled) for day, time, enabled in ret]


@with_connection(CONN_INFO)
def update(connection):
    cursor = connection.cursor()

    def get_db_version() -> int:
        version = 0
        try:
            sql = "SELECT * FROM db_version"
            cursor.execute(sql)
            if cursor.rowcount == 1:
                version, = cursor.fetchone()
        except psycopg2.DatabaseError as e:
            logger.error(f"Version table does not exist.")
            connection.rollback()
        return version

    logger.info("Update the database.")
    db_version = get_db_version()
    logger.info(f"Database version: {db_version}")
    while True:
        db_version = get_db_version()
        if db_version == 0:
            logger.info(f"Initialize the database the first time.")
            cursor.execute(f"""
            CREATE TYPE "day_type" AS ENUM (
              'Monday',
              'Tuesday',
              'Wednesday',
              'Thursday',
              'Friday',
              'Saturday',
              'Sunday'
            );
            CREATE TYPE "question_type" AS ENUM (
              '0_na',
              '1_retrospect',
              '2_outlook',
              '3_blocking'
            );
            CREATE TABLE "db_version" (
              "version" int NOT NULL
            );
            CREATE TABLE "teams" (
              "id" SERIAL PRIMARY KEY,
              "name" varchar UNIQUE,
              "space" varchar
            );
            CREATE TABLE "users" (
              "id" SERIAL PRIMARY KEY,
              "google_id" varchar UNIQUE,
              "space" varchar UNIQUE,
              "name" varchar,
              "email" varchar UNIQUE,
              "avatar_url" varchar,
              "team_id" int,
              "active" boolean DEFAULT True
            );
            CREATE TABLE "standups" (
              "id" SERIAL PRIMARY KEY,
              "user_id" int,
              "question_type" question_type DEFAULT '0_na',
              "answer" varchar,
              "added" timestamp DEFAULT NOW(),
              "message_id" varchar
            );
            CREATE TABLE "schedules" (
              "id" SERIAL PRIMARY KEY,
              "user_id" int,
              "day" day_type,
              "enabled" boolean DEFAULT True,
              "time" time DEFAULT '09:00:00'
            );
            ALTER TABLE "users" ADD FOREIGN KEY ("team_id") REFERENCES "teams" ("id");
            ALTER TABLE "standups" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");
            ALTER TABLE "schedules" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");
            CREATE UNIQUE INDEX ON "schedules" ("user_id", "day");
            INSERT INTO db_version VALUES({DB_VERSION});
            """)
            connection.commit()
        if db_version >= DB_VERSION:
            break
