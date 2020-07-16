from flask_socketio import send, join_room, leave_room, emit

from app import socketio
from app import db
import model


@socketio.on('join_game')
def on_join(username, game_id):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    if game.players is None or len(game.players) < 10:
        player = model.Player(name=username)
        player.game = game
        db.session.add(player)
        db.session.commit()
        join_room(game_id)
        emit('player_joined', player.id, room=game_id)


@socketio.on('leave_game')
def on_leave(player_id, game_id):
    db.session.query(model.Player).filter(model.Player.id == player_id).delete()
    db.session.commit()
    leave_room(game_id)
    send(str(player_id) + ' has left the game.', room=game_id)


@socketio.on('start_game')
def on_start(player_id):
    game = db.session.query(model.Game) \
        .filter(model.Game.host_id == player_id).first()
    if game is not None:
        game.next()


@socketio.on('create_game')
def on_create_game(username):
    game = model.Game()
    player = model.Player(name=username, game=game)
    game.host = player

    db.session.add(game)
    db.session.add(player)
    db.session.commit()
    join_room(game.id)
    emit('game_created', game.id)
    emit('player_joined', player.id, room=game.id)


@socketio.on('make_proposal')
def on_proposal(info):
    game_id = info['game_id']
    players_ids = info['players_id']
    mission = db.session.query(model.Game.missions) \
        .filter(model.Game.id == game_id).first()[-1]
    if mission is not None:
        mission.next(players_ids)


@socketio.on('vote')
def on_vote(info):
    result = info['result']
    voting_id = info['voting_id']
    voter_id = info['voter_id']

    voting = db.session.query(model.Voting) \
        .filter(model.Voting.id == voting_id).first()
    if voting is not None:
        voting.vote(voter_id, result)

