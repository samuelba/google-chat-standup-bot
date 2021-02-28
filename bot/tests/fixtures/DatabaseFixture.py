import pytest

import bot.utils.Database as Database


@pytest.fixture
def database_fixture(monkeypatch, request):
    def finalizer():
        destroy_database()
    request.addfinalizer(finalizer)

    monkeypatch.setattr(Database.CONN_INFO, 'host', 'postgres')
    monkeypatch.setattr(Database.CONN_INFO, 'port', '5432')
    monkeypatch.setattr(Database.CONN_INFO, 'user', 'postgres')
    monkeypatch.setattr(Database.CONN_INFO, 'password', 'postgres')
    monkeypatch.setattr(Database.CONN_INFO, 'dbname', 'postgres')

    create_database()
    yield


@Database.with_connection(Database.CONN_INFO)
def create_database(connection):
    cursor = connection.cursor()
    pass


@Database.with_connection(Database.CONN_INFO)
def destroy_database(connection):
    pass
