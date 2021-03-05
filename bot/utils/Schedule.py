class Schedule:
    __slots__ = ['id_', 'day', 'time', 'enabled']

    def __init__(self, id_: int, day: str, time: str, enabled: bool):
        self.id_ = id_
        self.day = day
        self.time = time
        self.enabled = enabled
