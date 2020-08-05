from sqlalchemy.exc import IntegrityError

import errors
import model
from app import db


def db_commit(function):
    def func(*args, **kwargs):
        try:
            result = function(*args, **kwargs)
            db.session.commit()
            return result
        except IntegrityError as err:
            db.session.rollback()
            raise errors.ForbiddenAction()

    return func


class GameManager:

    # Getters

    def configure(self, rules):
        self.max_players = max(rules.keys())

    def request_game(self, id):
        return db.session.query(model.Game).filter(model.Game.id == id).first()

    def request_games(self):
        return db.session.query(model.Game).all()

    def request_player(self, id):
        return db.session.query(model.Player).filter(model.Player.id == id).first()

    # Setters

    @db_commit
    def create_game(self, host_name, sid):
        game = model.Game()
        player = model.Player(name=host_name, sid=sid, game=game)
        game.host = player
        db.session.add(game)
        db.session.add(player)

        return game

    @db_commit
    def join_game(self, game_id, name, sid):
        if len(db.session.query(model.Player.id).filter(model.Player.game_id == game_id).all()) == self.max_players:
            raise errors.GameFull()
        player = model.Player(name=name, sid=sid, game_id=game_id)
        db.session.add(player)
        return player

    @db_commit
    def leave_game(self, game_id, sid, player_id):

        player = db.session.query(model.Player).filter(db.and_(model.Player.sid == sid,
                                                               model.Player.game_id == game_id)).first()
        if player is None:
            raise errors.UknownPlayer()
        # Player wants to leave
        if player.id == player_id:

            db.session.query(model.Player).filter(db.and_(model.Player.sid == sid,
                                                          model.Player.game_id == game_id)).delete()
            db.session.query(model.Game).filter(model.Game.host_id == player.id).delete()

        # Player wants to kick
        elif db.session.query(model.Game).filter(db.and_(model.Game.host_id == player.id,
                                                         model.Game.id == game_id)).first() is not None:
            db.session.query(model.Player).filter(db.and_(model.Player.id == player_id,
                                                          model.Player.game_id == game_id)).delete()
        else:
            raise errors.ForbiddenAction()

    @db_commit
    def delete_game(self, game_id, sid):

        player_id = db.session.query(model.Player.id).filter(db.and_(model.Player.sid == sid,
                                                                     model.Player.game_id == game_id)).first()

        if player_id is None:
            raise errors.UknownPlayer()
        elif db.session.query(model.Game).filter(db.and_(model.Game.host_id == player_id[0],
                                                         model.Game.id == game_id)).first() is None:
            raise errors.ForbiddenAction()

        db.session.query(model.Game).filter(model.Game.host_id == player_id[0]).delete()
