import bot.utils.Database as Database
from bot.utils.User import User

from bot.tests.fixtures.DatabaseFixture import database_fixture


def _add_users():
    john = User(0, 'abc', 'John Doe', 'john.doe@example.com', 'https://example.com/john-doe.png', 'space/abc', True,
                'Backend')
    Database.add_user(user=john)
    jane = User(0, 'def', 'Jane Doe', 'jane.doe@example.com', 'https://example.com/jane-doe.png', 'space/def', True,
                'Frontend')
    Database.add_user(user=jane)
    tim = User(0, 'ghi', 'Tim Doe', 'tim.doe@example.com', 'https://example.com/tim-doe.png', 'space/ghi', True,
               'Frontend')
    Database.add_user(user=tim)


def _add_teams():
    assert Database.add_team(team_name='Frontend')
    assert Database.add_team(team_name='Backend')


def test_add_team(database_fixture):
    # Test empty case.
    assert len(Database.get_teams()) == 0

    # Add teams.
    _add_teams()

    # Get all teams.
    teams = Database.get_teams()
    assert len(teams) == 2
    assert teams[0].name == 'Backend'
    assert teams[1].name == 'Frontend'

    # Check adding existing team.
    assert not Database.add_team(team_name='Backend')


def test_remove_team(database_fixture):
    # Test empty case.
    assert not Database.remove_team(team_name='')

    # Add teams.
    _add_teams()
    # Add users.
    _add_users()

    # Join team.
    assert Database.join_team(google_id='abc', team_name='Backend')

    # Remove teams.
    assert Database.remove_team(team_name='Frontend')
    assert not Database.remove_team(team_name='Backend')


def test_add_user(database_fixture):
    # Test empty case.
    assert len(Database.get_users(team_name='')) == 0

    # Add users.
    _add_users()

    # Get all users.
    users = Database.get_users(team_name='')
    assert len(users) == 3
    assert users[0].name == 'Jane Doe'
    assert users[1].name == 'John Doe'
    assert users[2].name == 'Tim Doe'

    # Add user again, this is to check the update function.
    jane = User(0, 'def', 'Jane Unknown', 'jane.doe@example.com', 'https://example.com/jane-doe.png', 'space/def', True,
                'Frontend')
    Database.add_user(user=jane)
    # Get all users.
    users = Database.get_users(team_name='')
    assert len(users) == 3
    assert users[0].name == 'Jane Unknown'


def test_disable_user(database_fixture):
    # Test empty case.
    assert not Database.disable_user(User(0, 'none', '', '', '', '', True, ''))

    # Add teams.
    _add_teams()
    # Add users.
    _add_users()
    # Join team.
    assert Database.join_team(google_id='abc', team_name='Backend')
    # Get users.
    users = Database.get_users(team_name='')
    assert users[0].active and users[0].team_name is None
    assert users[1].active and users[1].team_name == 'Backend'

    # Disable users.
    assert Database.disable_user(User(0, 'abc', '', '', '', '', True, ''))
    assert Database.disable_user(User(0, 'def', '', '', '', '', True, ''))

    # Get users.
    users = Database.get_users(team_name='')
    assert not users[0].active and users[0].team_name is None
    assert not users[1].active and users[1].team_name is None


def test_join_team(database_fixture):
    # Add teams and users.
    _add_teams()
    _add_users()

    # Join team.
    assert not Database.join_team(google_id='abc', team_name='not existing')
    assert Database.join_team(google_id='abc', team_name='Backend')
    assert Database.join_team(google_id='def', team_name='Frontend')

    # Get users and check team.
    users = Database.get_users(team_name='')
    assert users[0].team_name == 'Frontend'
    assert users[1].team_name == 'Backend'
    assert users[2].team_name is None

    # Change team.
    assert Database.join_team(google_id='abc', team_name='Frontend')
    users = Database.get_users(team_name='')
    assert users[0].team_name == 'Frontend'
    assert users[1].team_name == 'Frontend'


def test_leave_team(database_fixture):
    # Add teams and users.
    _add_teams()
    _add_users()

    # Join team.
    assert Database.join_team(google_id='abc', team_name='Backend')
    assert Database.join_team(google_id='def', team_name='Frontend')

    # Leave team.
    assert not Database.leave_team(google_id='xxx')
    assert Database.leave_team(google_id='abc')
    assert Database.leave_team(google_id='def')

    # Get users and check team.
    users = Database.get_users(team_name='')
    assert users[0].team_name is None
    assert users[1].team_name is None
    assert users[2].team_name is None


def test_join_room_to_team(database_fixture):
    # Add teams.
    _add_teams()

    # Try in-existent team.
    assert not Database.join_room_to_team(team_name='xxx', space='abc')

    # Join room to team.
    assert Database.join_room_to_team(team_name='Backend', space='abc')
    assert not Database.join_room_to_team(team_name='Backend', space='xyz')
    teams = Database.get_teams()
    assert teams[0].name == 'Backend' and teams[0].space == 'abc'
    assert teams[1].name == 'Frontend' and teams[1].space is None

    # Join room to other team.
    assert Database.join_room_to_team(team_name='Frontend', space='abc')
    teams = Database.get_teams()
    assert teams[0].name == 'Backend' and teams[0].space is None
    assert teams[1].name == 'Frontend' and teams[1].space == 'abc'


def test_leave_team_with_room(database_fixture):
    # Add teams.
    _add_teams()

    # Try in-existent team.
    assert not Database.leave_team_with_room(space='xxx')

    # Join room to team.
    assert Database.join_room_to_team(team_name='Backend', space='abc')
    assert Database.join_room_to_team(team_name='Frontend', space='def')
    teams = Database.get_teams()
    assert teams[0].name == 'Backend' and teams[0].space == 'abc'
    assert teams[1].name == 'Frontend' and teams[1].space == 'def'

    # Leave team.
    assert Database.leave_team_with_room(space='abc')
    teams = Database.get_teams()
    assert teams[0].name == 'Backend' and teams[0].space is None
    assert teams[1].name == 'Frontend' and teams[1].space == 'def'
