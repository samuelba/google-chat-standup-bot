class Team:
    __slots__ = ['id_', 'name', 'space']

    def __init__(self, id_: int, name: str, space: str):
        self.id_ = id_
        self.name = name
        self.space = space
