from flask_socketio import send, join_room, leave_room, emit

import errors
import model
from app import db, socketio


@socketio.on('connect', namespace='/lobby')
def connect():
    print('connected')
    send('connected')


@socketio.on('query_games', namespace='/lobby')
def query_games(info):
    games = db.session.query(model.Game).filter(model.Game.stage == model.GameStage.pending).all()
    emit('game_list', [g.to_dict(include_details=False) for g in games], json=True)


@socketio.on('join_game', namespace='/lobby')
def on_join(info):
    game_id = info['game_id']
    username = info['username']
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    try:
        player = game.add_player(username)
        join_room(game_id)
        emit('game_updated', game.to_dict(), room=game.id, namespace='/game')
        send(f'{username} joined game')
        return {'game': game.to_dict(), 'player': player.to_dict()}
    except errors.GameError as err:
        emit('error', str(err))


@socketio.on('leave_game', namespace='/game')
def on_leave(info):
    player_id = info['player_id']
    game_id = info['game_id']
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    username = game.remove_player(player_id)
    leave_room(game_id)
    emit('game_updated', game.to_dict(), room=game.id)
    send(f'{username} left game')

@socketio.on('start_game', namespace='/game')
def on_start(player_id):
    game = db.session.query(model.Game) \
        .filter(model.Game.host_id == player_id).first()
    if game is not None:
        try:
            for action in game.update():
                action.execute()
            # emit('game_status_changed', {'status': game.status.name}, namespace='/games', broadcast=True)
        except errors.GameError as err:
            emit('error', str(err))
    else:
        emit('error', str(errors.GameNotFound()))


@socketio.on('create_game', namespace='/lobby')
def on_create_game(info):
    username = info['username']
    print('create_game')
    game = model.Game()
    db.session.add(game)
    db.session.commit()
    player = game.add_player(username, True)
    join_room(game.id)

    games = db.session.query(model.Game).filter(model.Game.stage == model.GameStage.pending).all()
    emit('game_list', [g.to_dict(include_details=False) for g in games], broadcast=True, json=True)
    return {'game': game.to_dict(), 'player': player.to_dict()}


@socketio.on('delete_game', namespace='/game')
def on_delete_game(info):
    player_id = info['player_id']
    game_id = info['game_id']
    game = db.session.query(model.Game).filter(
        db.and_(model.Game.id == game_id, model.Game.host_id == player_id)).first()
    if game is not None:
        db.session.query(model.Game).filter(
            db.and_(model.Game.id == game_id, model.Game.host_id == player_id)).delete()
        games = db.session.query(model.Game).filter(model.Game.stage == model.GameStage.pending).all()
        emit('game_list', [g.to_dict(include_details=False) for g in games], broadcast=True, json=True)
        return 'Game is deleted'
    else:
        emit('error', str(errors.GameNotFound()))


@socketio.on('make_proposal', namespace='/game')
def on_proposal(info):
    game_id = info['game_id']
    players_ids = info['players_id']
    game = db.session.query(model.Game) \
        .filter(model.Game.id == game_id).first()
    if game is not None:
        for action in game.update(mission_state=model.RoundStage.troop_proposal, players_ids=players_ids):
            action.execute()
    else:
        emit('error', str(errors.GameNotFound()))


@socketio.on('troop_vote', namespace='/game')
def on_troop_vote(info):
    result = info['result']
    game_id = info['game_id']
    voter_id = info['voter_id']

    game = db.session.query(model.Game) \
        .filter(model.Game.id == game_id).first()
    if game is not None:
        actions = game.update(model.RoundStage.troop_voting, result=result, player_id=voter_id)
        for action in actions:
            action.execute()
    else:
        emit('error', str(errors.GameNotFound()))


@socketio.on('mission_vote', namespace='/game')
def on_troop_vote(info):
    result = info['result']
    game_id = info['game_id']
    voter_id = info['voter_id']

    game = db.session.query(model.Game) \
        .filter(model.Game.id == game_id).first()
    if game is not None:
        actions = game.update(model.RoundStage.mission_voting, result=result, player_id=voter_id)
        for action in actions:
            action.execute()
    else:
        emit('error', str(errors.GameNotFound()))
