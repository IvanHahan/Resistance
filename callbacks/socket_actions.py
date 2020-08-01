from flask_socketio import emit


class Callback:
    def __init__(self, game_id):
        self.game_id = game_id

    def execute(self):
        pass


class GameComplete(Callback):
    def __init__(self, game_id, result, status):
        super().__init__(game_id)
        self.result = result
        self.status = status

    def execute(self):
        emit('game_status_changed', {'resistance_won': self.result,
                                     'status': self.status.name}, room=self.game_id)

        emit('game_status_changed', {'status': self.status.name}, namespace='/games')


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
    def __init__(self, game_id, candidates, voters):
        super().__init__(game_id)
        self.candidates = candidates
        self.voters = voters

    def execute(self):
        emit('start_voting', {'candidates': self.candidates,
                              'voters': self.voters}, room=self.game_id)


class MissionComplete(Callback):
    def __init__(self, game_id, result):
        super().__init__(game_id)
        self.result = result

    def execute(self):
        emit('mission_complete', self.result, room=self.game_id)
