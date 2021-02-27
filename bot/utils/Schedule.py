class Schedule:
    __slots__ = ['day', 'time', 'enabled']

    def __init__(self, day: str, time: str, enabled: bool):
        self.day = day
        self.time = time
        self.enabled = enabled
