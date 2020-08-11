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


@socketio.on('join_game', namespace='/lobby')
def on_join(info):
    game_id = info['game_id']
    username = info['username']
    try:
        player = game_manager.join_game(game_id, username, request.sid)
        game = game_manager.request_game(game_id)
        join_room(game_id, namespace='/game')
        emit('game_updated', game.to_dict(), room=game.id, broadcast=True, namespace='/game')
        return {'game': game.to_dict(), 'player': player.to_dict()}
    except errors.GameError as err:
        return str(err)


@socketio.on('create_game', namespace='/lobby')
def on_create_game(info):
    username = info['username']
    try:
        game = game_manager.create_game(username, request.sid)
        join_room(game.id, namespace='/game')
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             broadcast=True)
        return {'game': game.to_dict(), 'player': game.host.to_dict()}
    except errors.GameError as err:
        return str(err)
