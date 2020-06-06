from flask_socketio import send, join_room

from __main__ import socketio
from game import join_game, start_game, create_game, make_proposal, update_voting

@socketio.on('join')
def on_join(username, game_id):
    join_game(game_id, username)
    send(username + ' has entered the game.', game_id=game_id)


@socketio.on('leave')
def on_leave(username, game_id):
    join_room(game_id)
    send(username + ' has left the game.', game_id=game_id)


@socketio.on('start')
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
