import pytest

import bot.utils.Database as Database
from bot.utils.Logger import setup_logger


@pytest.fixture
def database_fixture(monkeypatch, request):
    setup_logger(True, '')

    def finalizer():
        destroy_database()
    request.addfinalizer(finalizer)

    # monkeypatch.setattr(Database.CONN_INFO, 'host', 'postgres')
    # monkeypatch.setattr(Database.CONN_INFO, 'port', '5432')
    # monkeypatch.setattr(Database.CONN_INFO, 'user', 'postgres')
    # monkeypatch.setattr(Database.CONN_INFO, 'password', 'postgres')
    # monkeypatch.setattr(Database.CONN_INFO, 'dbname', 'postgres')

    create_database()
    yield 'Database is initialized.'


def create_database():
    Database.update()
    pass


@Database.with_connection(Database.CONN_INFO)
def destroy_database(connection):
    cursor = connection.cursor()
    sql = "DROP TABLE schedules CASCADE;" \
          "DROP TABLE standups CASCADE;" \
          "DROP TABLE users CASCADE;" \
          "DROP TABLE teams CASCADE;" \
          "DROP TABLE db_version CASCADE;" \
          "DROP TYPE day_type CASCADE;" \
          "DROP TYPE question_type CASCADE;"
    cursor.execute(sql)
