from unittest import TestCase

from app import create_app, db
import model
import errors


class TestModel(TestCase):

    def setUp(self):
        self.app = create_app('config.Test')

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_game_start_insufficient_players(self):
        with self.app.app_context():
            game = model.Game()
            player1 = model.Player(name='1', game=game)
            player2 = model.Player(name='2', game=game)
            game.host = player1
            db.session.add(game)
            db.session.commit()
            with self.assertRaises(errors.InsufficientPlayersNumber):
                game.next()

    def test_game_start_sufficient_players(self):
        with self.app.app_context():
            game = model.Game()
            player1 = model.Player(name='1', game=game)
            player2 = model.Player(name='2', game=game)
            player3 = model.Player(name='3', game=game)
            game.host = player1
            db.session.add(game)
            db.session.commit()
            game.update()
            game.next()
            assert player1.role is not None
            assert player2.role is not None
            assert player3.role is not None
