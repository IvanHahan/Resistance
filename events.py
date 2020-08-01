from flask_socketio import send, join_room, leave_room, emit

import errors
import model
from app import db, socketio


@socketio.on('connect', namespace='/games')
def connect():
    games = db.session.query(model.Game).filter(model.Game.stage == model.GameStage.pending).all()
    send('connected')
    send([g.to_dict(include_details=False) for g in games], json=True)


# @socketio.on('pidor', namespace='/test')
# def pidor(hui):
#     print('pidor', hui)
#     send('Ti pidor')
#     emit('pizda', ['hui'])
#     send({'hui': 'pizda'}, json=True)

@socketio.on('join_game', namespace='/games')
def on_join(info):
    game_id = info['game_id']
    username = info['username']
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    try:
        player = game.add_player(username)
        join_room(game_id)
        emit('player_joined', player.to_dict(), room=game_id)
    except errors.GameError as err:
        send(str(err))


@socketio.on('leave_game', namespace='/games')
def on_leave(info):
    player_id = info['player_id']
    game_id = info['game_id']
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    username = game.remove_player(player_id)
    leave_room(game_id)
    emit('player_left', username, room=game_id)


@socketio.on('start_game', namespace='/games')
def on_start(player_id):
    game = db.session.query(model.Game) \
        .filter(model.Game.host_id == player_id).first()
    if game is not None:
        try:
            for action in game.update():
                action.execute()
            emit('game_status_changed', {'status': game.status.name}, namespace='/games', broadcast=True)
            emit('game_status_changed', {'status': game.status.name}, room=game.id)
        except errors.GameError as err:
            send(str(err))
    else:
        send(str(errors.GameNotFound()))

@socketio.on('create_game', namespace='/games')
def on_create_game(username):
    game = model.Game()
    game.add_player(username, True)
    join_room(game.id)
    emit('game_created', game.to_dict(), broadcast=True, namespace='/games')


@socketio.on('delete_game', namespace='/games')
def on_delete_game(info):
    player_id = info['player_id']
    game_id = info['game_id']
    game = db.session.query(model.Game).filter(
        db.and_(model.Game.id == game_id, model.Game.host_id == player_id)).first()
    if game is not None:
        db.session.query(model.Game).filter(
            db.and_(model.Game.id == game_id, model.Game.host_id == player_id)).delete()
        emit('game_deleted', game.id, broadcast=True, namespace='/games')
    else:
        send(str(errors.GameNotFound()))


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
        send(str(errors.GameNotFound()))


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
        send(str(errors.GameNotFound()))


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
        send(str(errors.GameNotFound()))
