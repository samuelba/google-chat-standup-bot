import psycopg2
from typing import Optional, Sequence, Tuple

from bot.utils.Logger import logger
from bot.utils.Question import Question
from bot.utils.Schedule import Schedule
from bot.utils.Team import Team
from bot.utils.User import User


def add_user(connection, user: User) -> bool:
    with connection.cursor() as cursor:
        logger.debug(f"Add/update user: {user}")
        sql = "SELECT * " \
              "FROM users AS u " \
              "WHERE u.google_id = %s"
        cursor.execute(sql, (user.google_id,))
        ret = cursor.fetchall()
        if ret:
            logger.debug(f"Update user: {user}")
            sql = "UPDATE users " \
                  "SET name = %s, email = %s, avatar_url = %s, space = %s, active = %s " \
                  "WHERE google_id = %s " \
                  "RETURNING id"
            cursor.execute(sql, (user.name, user.email, user.avatar_url, user.space, True, user.google_id))
        else:
            logger.debug(f"Add new user: {user}")
            sql = "INSERT INTO users (google_id, name, email, avatar_url, space, active) " \
                  "VALUES (%s, %s, %s, %s, %s, %s) " \
                  "RETURNING id"
            cursor.execute(sql, (user.google_id, user.name, user.email, user.avatar_url, user.space, True))
        ret = cursor.fetchone()
        return ret is not None


def disable_user(connection, user: User) -> bool:
    with connection.cursor() as cursor:
        sql = "UPDATE users " \
              "SET active = %s, team_id = NULL " \
              "WHERE google_id = %s " \
              "RETURNING id"
        cursor.execute(sql, (False, user.google_id))
        ret = cursor.fetchone()
        return ret is not None


def add_team(connection, team_name: str) -> bool:
    with connection.cursor() as cursor:
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


def get_teams(connection) -> Sequence[Team]:
    with connection.cursor() as cursor:
        sql = "SELECT id, name, space " \
              "FROM teams " \
              "ORDER BY name ASC"
        cursor.execute(sql)
        ret = cursor.fetchall()
        return [Team(id_, name, space) for id_, name, space in ret]


def join_team(connection, google_id: str, team_name: str) -> bool:
    with connection.cursor() as cursor:
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


def leave_team(connection, google_id: str) -> bool:
    with connection.cursor() as cursor:
        sql = "UPDATE users " \
              "SET team_id = NULL " \
              "WHERE google_id = %s " \
              "RETURNING id"
        cursor.execute(sql, (google_id,))
        ret = cursor.fetchone()
        return ret is not None


def remove_team(connection, team_name: str) -> bool:
    with connection.cursor() as cursor:
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


def join_room_to_team(connection, team_name: str, space: str) -> bool:
    # Check if this team_name as already a space assigned.
    with connection.cursor() as cursor:
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
    leave_team_with_room(connection, space=space)

    # Add the space to the team.
    with connection.cursor() as cursor:
        sql = "UPDATE teams " \
              "SET space = %s " \
              "WHERE name = %s " \
              "RETURNING id"
        cursor.execute(sql, (space, team_name))
        ret = cursor.fetchone()
        return ret is not None


def leave_team_with_room(connection, space: str) -> bool:
    with connection.cursor() as cursor:
        sql = "UPDATE teams " \
              "SET space = NULL " \
              "WHERE space = %s" \
              "RETURNING id"
        cursor.execute(sql, (space,))
        ret = cursor.fetchone()
        return ret is not None


def get_team_of_user(connection, google_id: str) -> Optional[Team]:
    with connection.cursor() as cursor:
        sql = "SELECT t.id, t.name, t.space " \
              "FROM users AS u " \
              "INNER JOIN teams AS t ON t.id = u.team_id AND u.google_id = %s"
        cursor.execute(sql, (google_id,))
        ret = cursor.fetchone()
        if ret:
            id_, name, space = ret
            return Team(id_, name, space)
        return None


def get_users(connection, team_name: str) -> Sequence[User]:
    with connection.cursor() as cursor:
        team_join = "INNER" if team_name else "LEFT"
        team_filter = "AND t.name = %s" if team_name else ""
        team_filter_value = (team_name,) if team_name else ()
        sql = "SELECT u.id, u.google_id, u.name, u.email, u.avatar_url, u.space, u.active, t.name " \
              "FROM users AS u " \
              f"{team_join} JOIN teams AS t ON t.id = u.team_id {team_filter} " \
              "ORDER BY u.name ASC"
        cursor.execute(sql, team_filter_value)
        ret = cursor.fetchall()
        return [User(id_, google_id, name, email, avatar_url, space, active, team_name)
                for id_, google_id, name, email, avatar_url, space, active, team_name in ret]


def get_questions(connection, google_id: str) -> Sequence[Question]:
    with connection.cursor() as cursor:
        sql = "SELECT q.id, q.team_id, q.question, q.question_order " \
              "FROM questions AS q " \
              "INNER JOIN users AS u ON u.team_id = q.team_id AND u.google_id = %s " \
              "WHERE q.question_order != 0 " \
              "ORDER BY q.question_order ASC"
        cursor.execute(sql, (google_id,))
        ret = cursor.fetchall()
        if not ret:
            return []
        return [Question(id_, team_id, question, order) for id_, team_id, question, order in ret]


def add_question(connection, google_id: str, question: str) -> bool:
    team = get_team_of_user(connection, google_id=google_id)
    if not team:
        return False

    with connection.cursor() as cursor:
        sql = "INSERT INTO questions (team_id, question, question_order)" \
              "  SELECT q.team_id, %s, q.question_order + 1 " \
              "  FROM questions AS q " \
              "  WHERE q.team_id = %s " \
              "  ORDER BY q.question_order DESC " \
              "  LIMIT 1" \
              "ON CONFLICT DO NOTHING " \
              "RETURNING id"
        cursor.execute(sql, (question, team.id_))
        ret = cursor.fetchone()
        return ret is not None


def remove_question(connection, question_id: int) -> bool:
    with connection.cursor() as cursor:
        sql = "DELETE FROM questions " \
              "WHERE id = %s " \
              "RETURNING id"
        cursor.execute(sql, (question_id,))
        ret = cursor.fetchone()
        return ret is not None


def reorder_questions(connection, team_id: int, question_id: int, order_step: int) -> bool:
    with connection.cursor() as cursor:
        sql = "SELECT id " \
              "FROM questions " \
              "WHERE team_id = %s AND question_order >= %s " \
              "ORDER BY question_order DESC"
        cursor.execute(sql, (team_id, order_step))
        ret = cursor.fetchall()

        for id_, in ret:
            sql = "UPDATE questions " \
                  "SET question_order = question_order + 1 " \
                  "WHERE id = %s " \
                  "RETURNING id"
            cursor.execute(sql, (id_,))

        sql = "UPDATE questions " \
              "SET question_order = %s " \
              "WHERE id = %s " \
              "RETURNING id"
        cursor.execute(sql, (order_step, question_id))
        ret = cursor.fetchone()
        return ret is not None


def get_previous_question(connection, google_id: str) -> Optional[Question]:
    with connection.cursor() as cursor:
        sql = "SELECT q.id, q.team_id, q.question, q.question_order " \
              "FROM standups AS s " \
              "INNER JOIN questions AS q ON q.id = s.question_id " \
              "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s " \
              "WHERE s.added::date = NOW()::date " \
              "ORDER BY s.added DESC " \
              "LIMIT 1"
        cursor.execute(sql, (google_id,))
        ret = cursor.fetchone()
        if not ret:
            return None
        return Question(ret[0], ret[1], ret[2], ret[3])


def get_current_question(connection, google_id: str, previous_question: Question = None) -> Optional[Question]:
    if previous_question is None:
        previous_question = get_previous_question(connection, google_id=google_id)
        if not previous_question:
            return None

    with connection.cursor() as cursor:
        sql = "SELECT q.id, q.team_id, q.question, q.question_order " \
              "FROM questions AS q " \
              "INNER JOIN teams AS t ON t.id = q.team_id " \
              "INNER JOIN users AS u ON u.team_id = t.id AND u.google_id = %s " \
              "WHERE q.question_order > %s " \
              "ORDER BY q.question_order ASC " \
              "LIMIT 1"
        cursor.execute(sql, (google_id, previous_question.order))
        ret = cursor.fetchone()
        if not ret:
            return None
        return Question(ret[0], ret[1], ret[2], ret[3])


def reset_standup(connection, google_id: str) -> bool:
    with connection.cursor() as cursor:
        sql = "INSERT INTO standups (user_id, question_id, added) " \
              "SELECT u.id, q.id, NOW() " \
              "FROM users AS u " \
              "INNER JOIN teams AS t ON t.id = u.team_id " \
              "INNER JOIN questions AS q ON q.team_id = t.id AND q.question_order = 0 " \
              "WHERE u.google_id = %s " \
              "RETURNING id"
        cursor.execute(sql, (google_id,))
        ret = cursor.fetchone()
        return ret is not None


def add_standup_answer(connection, google_id: str, answer: str, current_question: Question = None) -> bool:
    if current_question is None:
        current_question = get_current_question(connection, google_id=google_id)
        if not current_question:
            return False

    with connection.cursor() as cursor:
        sql = "INSERT INTO standups (user_id, question_id, answer, added) " \
              "SELECT u.id, %s, %s, NOW() " \
              "FROM users AS u " \
              "WHERE u.google_id = %s " \
              "RETURNING standups.id"
        cursor.execute(sql, (current_question.id_, answer, google_id))
        ret = cursor.fetchone()
        return ret is not None


def get_standup_answers(connection, google_id: str) -> Sequence[Tuple]:
    with connection.cursor() as cursor:
        sql = "SELECT DISTINCT ON(q.question_order) q.question_order, q.question, s.answer " \
              "FROM standups AS s " \
              "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s " \
              "INNER JOIN questions AS q ON q.id = s.question_id AND q.question_order != 0 " \
              "WHERE s.added::date = NOW()::date " \
              "ORDER BY q.question_order ASC, s.added DESC"
        cursor.execute(sql, (google_id,))
        ret = cursor.fetchall()
        if not ret:
            return dict()
        return [(question, answer) for order, question, answer in ret]


def get_standup_answer_message_id(connection, google_id: str) -> str:
    with connection.cursor() as cursor:
        sql = "SELECT s.message_id " \
              "FROM standups AS s " \
              "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s " \
              "WHERE s.added::date = NOW()::date AND s.message_id IS NOT NULL"
        cursor.execute(sql, (google_id,))
        ret = cursor.fetchone()
        if not ret:
            return ''
        message_id, = ret
        return message_id


def set_message_id(connection, google_id: str, message_id: str) -> bool:
    with connection.cursor() as cursor:
        sql = "UPDATE standups AS s " \
              "SET message_id = %s " \
              "FROM users AS u " \
              "WHERE s.user_id = u.id " \
              "      AND u.google_id = %s " \
              "      AND s.added::date = NOW()::date " \
              "RETURNING s.id"
        cursor.execute(sql, (message_id, google_id))
        ret = cursor.fetchone()
        return ret is not None


def get_users_with_schedule(connection, day: str, time: str) -> Sequence[User]:
    with connection.cursor() as cursor:
        sql = "SELECT DISTINCT ON(u.google_id) u.name, u.email, u.google_id, u.space, st.question_id " \
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
        return [User(0, google_id, name, email, '', space, True, '')
                for name, email, google_id, space, question_id in ret if question_id is None]


def enable_schedule(connection, google_id: str, day: str, enable: bool) -> bool:
    with connection.cursor() as cursor:
        sql = "UPDATE schedules AS s " \
              "SET enabled = %s " \
              "FROM users AS u " \
              "WHERE s.user_id = u.id AND u.google_id = %s AND s.day = %s " \
              "RETURNING s.id"
        cursor.execute(sql, (enable, google_id, day))
        ret = cursor.fetchone()
        return ret is not None


def update_schedule_time(connection, google_id: str, day: str, time: str) -> bool:
    with connection.cursor() as cursor:
        sql = "UPDATE schedules AS s " \
              "SET time = %s " \
              "FROM users AS u " \
              "WHERE s.user_id = u.id AND u.google_id = %s AND s.day = %s " \
              "RETURNING s.id"
        cursor.execute(sql, (time, google_id, day))
        ret = cursor.fetchone()
        return ret is not None


def get_schedules(connection, google_id: str) -> Sequence[Schedule]:
    with connection.cursor() as cursor:
        sql = "SELECT s.id, s.day, s.time, s.enabled " \
              "FROM schedules AS s " \
              "INNER JOIN users AS u ON u.id = s.user_id AND u.google_id = %s"
        cursor.execute(sql, (google_id,))
        ret = cursor.fetchall()
        return [Schedule(id_, day, time, enabled) for id_, day, time, enabled in ret]


def update(connection) -> bool:

    def get_schema_version() -> int:
        version = 0
        try:
            with connection.cursor() as curs:
                curs.execute("SELECT version FROM __schema_version")
                if curs.rowcount == 1:
                    version, = curs.fetchone()
        except psycopg2.DatabaseError:
            logger.error("Version table does not exist.")
            connection.rollback()
        return version

    with connection.cursor() as cursor:
        import bot.utils.storage.DatabaseSchema as DatabaseSchema

        logger.info("Update the schema.")
        schema_version = get_schema_version()
        logger.info(f"Schema version before the migration: {schema_version}")
        for step in range(schema_version, len(DatabaseSchema.migrations)):
            for statement in DatabaseSchema.migrations[step]:
                cursor.execute(statement)
            connection.commit()
        schema_version = get_schema_version()
        logger.info(f"Schema version after the migration: {schema_version}")

    return True
