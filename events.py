from flask_socketio import send, join_room, leave_room, rooms, emit

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
        emit('player_joined', username, room=game_id)


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
def on_proposal(mission_id, players_ids):
    mission = db.session.query(model.Mission) \
        .filter(model.Mission.id == mission_id).first()
    if mission is not None:
        mission.next(players_ids)


@socketio.on('vote')
def on_vote(voting_id, player_id, result):
    voting = db.session.query(model.Voting) \
        .filter(model.Voting.id == voting_id).first()
    if voting is not None:
        voting.vote(player_id, result)

