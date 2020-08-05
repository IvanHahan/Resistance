import errors
import model
from unittest import TestCase
from app import create_app, db, game_manager
from game_manager import GameManager
from sqlalchemy.exc import IntegrityError


class TestGameManager(TestCase):

    def setUp(self):
        self.app = create_app('config.Test')

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_create_game_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            self.assertTrue(game.host is not None)
            self.assertTrue(len(db.session.query(model.Game).all()) == 1)
            self.assertTrue(len(db.session.query(model.Player).all()) == 1)

    def test_join_game_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game.id, 'test1', '2')
            self.assertTrue(len(db.session.query(model.Player)
                                .filter(model.Player.game_id == game.id).all()) == 2)

    def test_join_game_equal_name_fail(self):
        with self.app.app_context():
            with self.assertRaises(errors.ForbiddenAction):
                game = game_manager.create_game('test', '1')
                game_manager.join_game(game.id, 'test', '2')

    def test_join_game_equal_sid_fail(self):
        with self.app.app_context():
            with self.assertRaises(errors.ForbiddenAction):
                game = game_manager.create_game('test', '1')
                game_manager.join_game(game.id, 'test1', '1')

    def test_join_game_full_fail(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game.id, 'test1', '2')
            game_manager.join_game(game.id, 'test2', '3')
            with self.assertRaises(errors.GameFull):
                game_manager.join_game(game.id, 'test3', '4')

    def test_leave_game_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game.id, 'test1', '2')
            game_manager.leave_game(game.id, '2', 2)
            self.assertTrue(len(db.session.query(model.Player)
                                .filter(model.Player.game_id == game.id).all()) == 1)
            self.assertTrue(len(db.session.query(model.Player).all()) == 1)
            self.assertTrue(len(db.session.query(model.Game).all()) == 1)

    def test_leave_game_host_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game.id, 'test1', '2')
            game_manager.leave_game(game.id, '1', 1)
            self.assertTrue(len(db.session.query(model.Game).all()) == 0)
            self.assertTrue(len(db.session.query(model.Player).all()) == 0)

    def test_kick_player_non_host_fail(self):
        with self.app.app_context():
            with self.assertRaises(errors.ForbiddenAction):
                game = game_manager.create_game('test', '1')
                game_manager.join_game(game.id, 'test1', '2')
                game_manager.leave_game(game.id, '2', 1)
            self.assertTrue(len(db.session.query(model.Player)
                                .filter(model.Player.game_id == game.id).all()) == 2)

    def test_kick_player_host_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game.id, 'test1', '2')
            game_manager.leave_game(game.id, '1', 2)
            self.assertTrue(len(db.session.query(model.Player)
                                .filter(model.Player.game_id == game.id).all()) == 1)
            self.assertTrue(len(db.session.query(model.Game).all()) == 1)

    def test_delete_game_host_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game.id, 'test1', '2')
            game_manager.delete_game(game.id, '1')
            self.assertTrue(len(db.session.query(model.Player).all()) == 0)
            self.assertTrue(len(db.session.query(model.Game).all()) == 0)

    def test_delete_game_non_host_fail(self):
        with self.app.app_context():
            with self.assertRaises(errors.ForbiddenAction):
                game = game_manager.create_game('test', '1')
                game_manager.join_game(game.id, 'test1', '2')
                game_manager.delete_game(game.id, '2')
            self.assertTrue(len(db.session.query(model.Player).all()) == 2)
            self.assertTrue(len(db.session.query(model.Game).all()) == 1)
