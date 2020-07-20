from flask_socketio import emit


class Callback:
    def __init__(self, game_id):
        self.game_id = game_id

    def execute(self):
        pass


class GamePaused(Callback):
    def __init__(self, game_id):
        super().__init__(game_id)

    def execute(self):
        emit('game_paused', self.game_id, room=self.game_id)


class GameResumed(Callback):
    def __init__(self, game_id):
        super().__init__(game_id)

    def execute(self):
        emit('game_resumed', self.game_id, room=self.game_id)


class GameComplete(Callback):
    def __init__(self, game_id, result):
        super().__init__(game_id)
        self.result = result

    def execute(self):
        emit('game_complete', self.result, room=self.game_id)


class QueryProposal(Callback):
    def __init__(self, game_id, leader_id, troop_size):
        super().__init__(game_id)
        self.leader_id = leader_id
        self.troop_size = troop_size

    def execute(self):
        emit('query_proposal', {'leader_id': self.leader_id,
                                'troop_size': self.troop_size
                                }, room=self.game_id)


class StartVoting(Callback):
    def __init__(self, game_id, voting_id, candidates, voters):
        super().__init__(game_id)
        self.voting_id = voting_id
        self.candidates = candidates
        self.voters = voters

    def execute(self):
        emit('start_voting', {'voting_id': self.voting_id,
                              'candidates': self.candidates,
                              'voters': self.voters}, room=self.game_id)


class MissionComplete(Callback):
    def __init__(self, game_id, result):
        super().__init__(game_id)
        self.result = result

    def execute(self):
        emit('mission_complete', self.result, room=self.game_id)
