class Question:
    __slots__ = ['id_', 'team_id', 'question', 'order']

    def __init__(self, id_: int, team_id: int, question: str, order: int):
        self.id_ = id_
        self.team_id = team_id
        self.question = question
        self.order = order
