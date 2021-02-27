class User:
    __slots__ = ['id_', 'google_id', 'name', 'email', 'avatar_url', 'space', 'active', 'team_name']

    def __init__(self, id_: int, google_id: str, name: str, email: str, avatar_url: str, space: str, active: bool,
                 team_name: str):
        self.id_ = id_
        self.google_id = google_id
        self.name = name
        self.email = email
        self.avatar_url = avatar_url
        self.space = space
        self.active = active
        self.team_name = team_name
