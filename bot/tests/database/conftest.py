import pytest

import bot.utils.storage.Storage as Storage
from bot.utils.Logger import setup_logger


@pytest.fixture
def database_fixture(request):
    setup_logger(True, '')

    def finalizer():
        destroy_database()
    request.addfinalizer(finalizer)

    create_database()
    yield 'Database is initialized.'


def create_database():
    Storage.update()


@Storage.transact
def destroy_database(connection):
    with connection.cursor() as cursor:
        sql = "DROP TABLE schedules CASCADE;" \
              "DROP TABLE standups CASCADE;" \
              "DROP TABLE questions CASCADE;" \
              "DROP TABLE users CASCADE;" \
              "DROP TABLE teams CASCADE;" \
              "DROP TABLE __schema_version CASCADE;" \
              "DROP TYPE day_type CASCADE;"
        cursor.execute(sql)
