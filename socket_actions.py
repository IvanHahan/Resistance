from flask_socketio import emit


def game_paused(game_id):
    def func():
        emit('game_paused', game_id, room=game_id)

    return func


def game_resumed(game_id):
    def func():
        emit('game_resumed', game_id, room=game_id)

    return func


def game_complete(game_id, result):
    def func():
        emit('game_complete', result, room=game_id)

    return func


def query_proposal(game_id, leader_id, troop_size):
    def func():
        emit('query_proposal', {'leader_id': leader_id,
                                'troop_size': troop_size
                                }, room=game_id)

    return func


def start_voting(game_id, voting_id, candidates, voters):
    def func():
        emit('start_voting', {'voting_id': voting_id,
                              'candidates': candidates,
                              'voters': voters}, room=game_id)

    return func


def mission_complete(game_id, result):
    def func():
        emit('mission_complete', result, room=game_id)

    return func
