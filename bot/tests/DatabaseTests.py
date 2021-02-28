import bot.utils.Database as Database

from bot.tests.fixtures.DatabaseFixture import database_fixture


def test_something(database_fixture):
    print(database_fixture)
    assert Database.add_team(team_name='Frontend')
    teams = Database.get_teams()
    assert len(teams) == 1
    assert teams[0].name == 'Frontend'
