from flask_socketio import send, join_room, leave_room, rooms, emit

from __main__ import socketio
from game import join_game, start_game, create_game, make_proposal, update_voting, leave_game


@socketio.on('join_game')
def on_join(username, game_id):
    player_id = join_game(game_id, username)
    send(username + ' has joined the game', room=game_id)
    emit('player_joined', player_id)


@socketio.on('leave_game')
def on_leave(player_id, game_id):
    leave_game(player_id, game_id)
    send(str(player_id) + ' has left the game.', room=game_id)


@socketio.on('start_game')
def on_start(game_id):
    start_game(game_id)


@socketio.on('create_game')
def on_create_game(username):
    create_game(username)


@socketio.on('proposal')
def on_proposal(mission_id, players_ids):
    make_proposal(mission_id, players_ids)


@socketio.on('vote')
def on_vote(voting_id, player_id, result):
    update_voting(voting_id)
