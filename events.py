from flask_socketio import send, join_room, leave_room, emit
from sqlalchemy.exc import IntegrityError

import errors
import model
from app import db, socketio
from flask import request


def verify_player(player_id):
    if db.session.query(model.Player.sid).filter(db.and_(model.Player.id == player_id,
                                                       model.Player.sid == request.sid)).first() is None:
        raise errors.ForbiddenAction()

@socketio.on('connect', namespace='/lobby')
def connect():
    print(request.sid)
    print('connected')
    send('connected')


@socketio.on('query_games', namespace='/lobby')
def query_games(info):
    games = db.session.query(model.Game).filter(model.Game.stage == model.GameStage.pending).all()
    emit('game_list', [g.to_dict(include_details=False) for g in games], json=True)


@socketio.on('join_game', namespace='/lobby')
def on_join(info):
    print('join_game')
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


@socketio.on('leave_game', namespace='/game')
def on_leave(info):
    print('leave_game')
    game_id = info['game_id']
    player_id = info['player_id']
    try:
        player = game_manager.request_player(player_id)
        game_manager.leave_game(game_id, request.sid, player_id)
        game = game_manager.request_game(game_id)
        leave_room(game.id, sid=player.sid)
        emit('game_updated', game.to_dict(), room=game_id, broadcast=True)
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             namespace='/lobby', broadcast=True)
        return 'You left game'
    except errors.GameError as err:
        return str(err)


@socketio.on('start_game', namespace='/game')
def on_start(player_id):
    game = db.session.query(model.Game) \
        .filter(model.Game.host_id == player_id).first()
    try:
        verify_player(player_id)
        if game is not None:
            try:
                for action in game.update():
                    action.execute()
                # emit('game_status_changed', {'status': game.status.name}, namespace='/games', broadcast=True)
            except errors.GameError as err:
                return str(err)
        else:
            raise errors.GameNotFound()
    except errors.GameError as err:
        return str(err)


@socketio.on('create_game', namespace='/lobby')
def on_create_game(info):
    username = info['username']
    print('create_game')
    try:
        game = game_manager.create_game(username, request.sid)
        join_room(game.id, namespace='/game')
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             broadcast=True)
        return {'game': game.to_dict(), 'player': game.host.to_dict()}
    except errors.GameError as err:
        return str(err)

@socketio.on('delete_game', namespace='/game')
def on_delete_game(info):
    print('delete_game')
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
    player_id = info['leader_id']
    game_id = info['game_id']
    players_ids = info['players_id']

    try:
        verify_player(player_id)
        game = db.session.query(model.Game) \
            .filter(model.Game.id == game_id).first()
        if game is not None:
            for action in game.update(mission_state=model.RoundStage.troop_proposal, players_ids=players_ids):
                action.execute()
        else:
            raise str(errors.GameNotFound())
    except errors.GameError as err:
        return str(err)


@socketio.on('troop_vote', namespace='/game')
def on_troop_vote(info):
    result = info['result']
    game_id = info['game_id']
    voter_id = info['voter_id']

    try:
        verify_player(voter_id)
        game = db.session.query(model.Game) \
            .filter(model.Game.id == game_id).first()

        if game is not None:
            actions = game.update(model.RoundStage.troop_voting, result=result, player_id=voter_id)
            for action in actions:
                action.execute()
        else:
            raise str(errors.GameNotFound())
    except errors.GameError as err:
        return str(err)


@socketio.on('mission_vote', namespace='/game')
def on_troop_vote(info):
    result = info['result']
    game_id = info['game_id']
    voter_id = info['voter_id']

    try:
        verify_player(voter_id)
        game = db.session.query(model.Game) \
            .filter(model.Game.id == game_id).first()
        if game is not None:
            actions = game.update(model.RoundStage.mission_voting, result=result, player_id=voter_id)
            for action in actions:
                action.execute()
        else:
            raise errors.GameNotFound()
    except errors.GameError as err:
        return str(err)
