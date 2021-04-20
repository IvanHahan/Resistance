import errors
import model
from unittest import TestCase
from app import create_app, db, game_manager
import numpy as np
np.random.seed(13)


class TestGameSetupStart(TestCase):

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
            game_manager.join_game(game, 'test1', '2')
            self.assertTrue(len(db.session.query(model.Player)
                                .filter(model.Player.game_id == game.id).all()) == 2)

    def test_join_game_equal_name_fail(self):
        with self.app.app_context():
            with self.assertRaises(errors.ForbiddenAction):
                game = game_manager.create_game('test', '1')
                game_manager.join_game(game, 'test', '2')

    def test_join_game_equal_sid_fail(self):
        with self.app.app_context():
            with self.assertRaises(errors.ForbiddenAction):
                game = game_manager.create_game('test', '1')
                game_manager.join_game(game, 'test1', '1')

    def test_join_game_full_fail(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.join_game(game, 'test3', '4')
            with self.assertRaises(errors.GameFull):
                game_manager.join_game(game, 'test4', '5')

    def test_join_game_started_fail(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            self.assertTrue(game.stage != model.GameStage.pending)
            with self.assertRaises(errors.ForbiddenAction):
                game_manager.join_game(game, 'test3', '4')
            self.assertTrue(len(game.players) == 3)

    def test_leave_game_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.leave_game(game.id, '2', 2)
            self.assertTrue(len(db.session.query(model.Player)
                                .filter(model.Player.game_id == game.id).all()) == 1)
            self.assertTrue(len(db.session.query(model.Player).all()) == 1)
            self.assertTrue(len(db.session.query(model.Game).all()) == 1)

    def test_leave_game_host_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.leave_game(game.id, '1', 1)
            self.assertTrue(len(db.session.query(model.Game).all()) == 0)
            self.assertTrue(len(db.session.query(model.Player).all()) == 0)

    def test_leave_game_started_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            self.assertTrue(game.stage != model.GameStage.pending)
            game_manager.leave_game(game.id, '2', 2)
            self.assertTrue(game.stage == model.GameStage.pending)
            self.assertTrue(len(game.missions) == 0)
            self.assertTrue(len(game.players) == 2)
            game_manager.join_game(game, 'test1', '2')
            game_manager.update_game(game, sid='1')
            self.assertTrue(game.stage != model.GameStage.pending)

    def test_kick_player_non_host_fail(self):
        with self.app.app_context():
            with self.assertRaises(errors.ForbiddenAction):
                game = game_manager.create_game('test', '1')
                game_manager.join_game(game, 'test1', '2')
                game_manager.leave_game(game.id, '2', 1)
            self.assertTrue(len(db.session.query(model.Player)
                                .filter(model.Player.game_id == game.id).all()) == 2)

    def test_kick_player_host_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.leave_game(game.id, '1', 2)
            self.assertTrue(len(db.session.query(model.Player)
                                .filter(model.Player.game_id == game.id).all()) == 1)
            self.assertTrue(len(db.session.query(model.Game).all()) == 1)

    def test_delete_game_host_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.try_delete_game(game.id, '1')
            self.assertTrue(len(db.session.query(model.Player).all()) == 0)
            self.assertTrue(len(db.session.query(model.Game).all()) == 0)

    def test_delete_game_non_host_fail(self):
        with self.app.app_context():
            with self.assertRaises(errors.ForbiddenAction):
                game = game_manager.create_game('test', '1')
                game_manager.join_game(game, 'test1', '2')
                game_manager.try_delete_game(game.id, '2')
            self.assertTrue(len(db.session.query(model.Player).all()) == 2)
            self.assertTrue(len(db.session.query(model.Game).all()) == 1)

    def test_start_game_host_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            self.assertTrue(game.stage == model.GameStage.executing_mission)

    def test_start_game_non_host_fail(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            with self.assertRaises(errors.ForbiddenAction):
                game_manager.update_game(game, sid='2')
            self.assertTrue(game.stage == model.GameStage.pending)

    def test_start_game_not_enough_players_fail(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            with self.assertRaises(errors.InsufficientPlayersNumber):
                game_manager.update_game(game, sid='1')
            self.assertTrue(game.stage == model.GameStage.pending)

    def test_restart_game_host_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            new_game = game_manager.new_game(game, sid='1')
            self.assertTrue(len(game.players) == 3)
            self.assertTrue(len(new_game.players) == 3)
            self.assertTrue(new_game.stage == model.GameStage.pending)

    def test_delete_game_inactive_players_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            for p in game.players:
                game_manager.deactivate_player(p)
            self.assertTrue(len(db.session.query(model.Game).all()) == 0)
            self.assertTrue(len(db.session.query(model.Player).all()) == 0)

    def test_delete_game_reactivate_players_success(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            p = game_manager.join_game(game, 'test2', '3')
            game_manager.deactivate_player(p)
            game_manager.activate_player(p)
            game_manager.update_game(game, sid='1')
            self.assertTrue(game.stage == model.GameStage.executing_mission)

    def test_multiple_spies_setup(self):
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.join_game(game, 'test3', '4')
            game_manager.update_game(game, sid='1')
            self.assertEqual(len(game.spies), game_manager.rules['team'][4]['spies'], 'Spies number do not match')


