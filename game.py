import model
from app import db
from flask import current_app as app
import numpy as np
from flask_socketio import emit, join_room, leave_room, send


def create_game(username):
    game = model.Game()
    player = model.Player(name=username, game=game)
    game.host = player

    db.session.add(game)
    db.session.add(player)
    db.session.commit()
    join_room(game.id)
    send('joined_game')


def join_game(game_id, username):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    if game.players is None or len(game.players) < 10:
        player = model.Player(name=username)
        player.game = game
        db.session.add(player)
        db.session.commit()
        join_room(game_id)
        return player.id


def leave_game(player_id, game_id):
    db.session.query(model.Player).filter(model.Player.id == player_id).delete()
    db.session.commit()
    leave_room(game_id)


def start_game(game_id):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    game.next()
