from flask_socketio import emit
import model


class Callback:
    def __init__(self, game_id):
        self.game_id = game_id

    def execute(self):
        pass


class GameUpdated(Callback):
    def __init__(self, game_dict):
        super().__init__(game_dict['id'])
        self.game_dict = game_dict

    def execute(self):
        emit('game_updated', self.game_dict, room=self.game_id, namespace='/game')


class MissionUpdated(Callback):
    def __init__(self, game_id, mission_dict):
        super().__init__(game_id)
        self.mission_dict = mission_dict

    def execute(self):
        emit('mission_updated', self.mission_dict, room=self.game_id)


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


class GameDeleted(Callback):
    def execute(self):
        emit('game_updated', 'Game deleted', room=self.game_id, namespace='/game')