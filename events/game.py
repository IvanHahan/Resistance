from flask import request
from flask_socketio import leave_room, emit

import errors
from app import socketio
from game_manager import shared as game_manager



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
        return str(err)


@socketio.on('start_game', namespace='/game')
def on_start(info):
    game_id = info['game_id']
    try:
        game = game_manager.request_game(game_id)
        game_manager.update_game(game, sid=request.sid).execute()
        return 'Game started'
    except errors.GameError as err:
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
        return str(err)


@socketio.on('make_proposal', namespace='/game')
def on_proposal(info):
    game_id = info['game_id']
    players_ids = info['players_id']
    try:
        game = game_manager.request_player(game_id)
        game_manager.update_game(game, players_ids=players_ids, sid=request.sid)
        return 'Proposal made'
    except errors.GameError as err:
        return str(err)


@socketio.on('vote', namespace='/game')
def on_vote(info):
    result = info['result']
    game_id = info['game_id']
    try:
        game = game_manager.request_player(game_id)
        game_manager.update_game(game, result=result, sid=request.sid).execute()
        return 'Vote made'
    except errors.GameError as err:
        return str(err)
