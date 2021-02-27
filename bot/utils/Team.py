class Team:
    __slots__ = ['name', 'webhook']

    def __init__(self, name: str, webhook: str):
        self.name = name
        self.webhook = webhook
