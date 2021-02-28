import bot.utils.Database as Database

from bot.tests.fixtures import DatabaseFixture


def test_something():
    Database.add_team(team_name='Frontend')
    teams = Database.get_teams()
    assert len(teams) == 1
    assert teams[0].name == 'Frontend'
