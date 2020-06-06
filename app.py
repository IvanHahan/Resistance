import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from game import join_game, start_game, create_game, make_proposal, update_voting

app = Flask(__name__)
app.config.from_object('config.Default')

db = SQLAlchemy(app)
db.create_all()

socketio = SocketIO(app)


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


@socketio.on('create')
def on_create(username):
    create_game(username)


@socketio.on('proposal')
def on_proposal(mission_id, players_ids):
    update_mission
    make_proposal(mission_id, players_ids)


@socketio.on('vote')
def on_vote(voting_id, player_id, result):
    update_voting(voting_id)



if __name__ == '__main__':
    socketio.run(app)