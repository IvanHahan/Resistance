from flask import request
from flask_socketio import send, join_room, leave_room, emit

import errors
from services import socketio, event_logger, game_manager


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
        event_logger.error(str(err))
        return str(err)


@socketio.on('leave_game', namespace='/game')
def on_leave(info):
    game_id = info['game_id']
    player_id = info['player_id']
    try:
        player = game_manager.request_player(player_id)
        game_manager.leave_game(game_id, request.sid, player_id)
        game = game_manager.request_game(game_id)
        emit('game_updated', game.to_dict(), room=game_id, broadcast=True, namespace='/game')
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             namespace='/lobby', broadcast=True)
        leave_room(game.id, sid=player.sid)
        return 'You left game'
    except errors.GameError as err:
        event_logger.error(str(err))
        return str(err)


@socketio.on('start_game', namespace='/game')
def on_start(info):
    game_id = info['game_id']
    try:
        game = game_manager.request_game(game_id)
        game_manager.update_game(game, sid=request.sid).execute()
        return 'Game started'
    except errors.GameError as err:
        event_logger.error(str(err))
        return str(err)


@socketio.on('create_game', namespace='/lobby')
def on_create_game(info):
    username = info['username']
    try:
        game = game_manager.create_game(username, request.sid)
        game_manager.join_game(game.id, 'liza', '1')
        game_manager.join_game(game.id, 'ivan2', '2')
        join_room(game.id, namespace='/game')
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             broadcast=True)
        return {'game': game.to_dict(), 'player': game.host.to_dict()}
    except errors.GameError as err:
        event_logger.error(str(err))
        return str(err)


@socketio.on('delete_game', namespace='/game')
def on_delete_game(info):
    game_id = info['game_id']
    try:
        game_manager.delete_game(game_id, request.sid)
        emit('game_updated', 'Game deleted', room=game_id)
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             namespace='/lobby', broadcast=True)
        return 'Game deleted'
    except errors.GameError as err:
        event_logger.error(str(err))
        return str(err)


@socketio.on('make_proposal', namespace='/game')
def on_proposal(info):
    game_id = info['game_id']
    players_ids = info['players_id']
    try:
        game = game_manager.request_player(game_id)
        game_manager.update_game(game, players_ids=players_ids, sid=request.sid)
    except errors.GameError as err:
        event_logger.error(str(err))
        return str(err)


@socketio.on('vote', namespace='/game')
def on_vote(info):
    result = info['result']
    game_id = info['game_id']
    try:
        game = game_manager.request_player(game_id)
        game_manager.update_game(game, result=result, sid=request.sid).execute()
    except errors.GameError as err:
        event_logger.error(str(err))
        return str(err)
