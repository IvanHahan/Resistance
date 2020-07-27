from flask_socketio import send, join_room, leave_room, emit

import model
from app import db
from app import socketio


@socketio.on('connect')
def connect():
    games = db.session.query(model.Game).filter(model.Game.status == model.GameStatus.pending).all()
    send([g.to_dict(include_details=False) for g in games])


@socketio.on('join_game')
def on_join(info):
    game_id = info['game_id']
    username = info['username']
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    if db.session.query(model.Player.id).filter(db.and_(model.Player.game_id == game_id,
                                                     model.Player.id == info.get('player_id', -1))).first() is not None:
        join_room(game_id)
    else:
        if game.players is None or len(game.players) < 10:
            player = model.Player(name=username)
            player.game = game
            db.session.add(player)
            db.session.commit()
            join_room(game_id)
            emit('player_joined', player.to_dict(), room=game_id)
        else:
            send('the game is full')


@socketio.on('leave_game')
def on_leave(info):
    player_id = info['player_id']
    game_id = info['game_id']
    db.session.query(model.Player).filter(model.Player.id == player_id).delete()
    db.session.commit()
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    leave_room(game_id)
    emit('player_left', game.to_dict(), room=game_id)


@socketio.on('start_game')
def on_start(player_id):
    game = db.session.query(model.Game) \
        .filter(model.Game.host_id == player_id).first()
    if game is not None:
        for action in game.update():
            action.execute()


@socketio.on('create_game')
def on_create_game(username):
    game = model.Game()
    player = model.Player(name=username, game=game)
    game.host = player

    db.session.add(game)
    db.session.add(player)
    db.session.commit()
    join_room(game.id)
    emit('game_created', game.to_dict(), broadcast=True)


@socketio.on('make_proposal')
def on_proposal(info):
    game_id = info['game_id']
    players_ids = info['players_id']
    game = db.session.query(model.Game) \
        .filter(model.Game.id == game_id).first()
    if game is not None:
        for action in game.update(mission_state=model.RoundStage.troop_proposal, players_ids=players_ids):
            action.execute()


@socketio.on('troop_vote')
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


@socketio.on('mission_vote')
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

