from flask import request
from flask_socketio import join_room, emit

import errors
from app import socketio
from game_manager import shared as game_manager


@socketio.on('connect', namespace='/lobby')
def connect():
    return 'connected'


@socketio.on('query_games', namespace='/lobby')
def query_games(info):
    games = game_manager.request_games()
    emit('game_list', [g.to_dict(include_details=False) for g in games], json=True)
