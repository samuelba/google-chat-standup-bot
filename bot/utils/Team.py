class Team:
    __slots__ = ['name', 'space']

    def __init__(self, name: str, space: str):
        self.name = name
        self.space = space
