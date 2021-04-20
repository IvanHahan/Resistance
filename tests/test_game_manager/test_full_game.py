import errors
import model
from unittest import TestCase
from app import create_app, db, game_manager
import numpy as np
np.random.seed(13)


class TestGameProgress(TestCase):
    def setUp(self):
        self.app = create_app('config.Test')
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            self.game_id = game.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_second_mission_created(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            current_leader_sid = game.current_leader().sid
            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='1', result=True)
            self.assertTrue(len(game.missions) == 2)
            self.assertTrue(len(game.missions) == 2)
            self.assertTrue(game.current_leader().sid != current_leader_sid)

    def test_game_complete_resistance_won_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)

            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='1', result=True)

            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[1, 2])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='1', result=True)
            self.assertTrue(game.current_mission().stage == model.RoundStage.mission_voting)
            self.assertTrue(game.stage == model.GameStage.executing_mission)
            game_manager.update_game(game, sid='2', result=True)

            self.assertTrue(game.stage == model.GameStage.finished)
            self.assertTrue(game.resistance_won is True)


class TestProdGameProgress(TestCase):
    def setUp(self):
        self.app = create_app('config.TestProd')
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.join_game(game, 'test3', '4')
            game_manager.join_game(game, 'test4', '5')
            game_manager.join_game(game, 'test5', '6')
            game_manager.update_game(game, sid='1')
            self.game_id = game.id

    def test_game_complete_resistance_won_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)

            # 1
            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[1, 2])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='4', result=True)
            game_manager.update_game(game, sid='5', result=False)
            game_manager.update_game(game, sid='6', result=False)

            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)

            # 2
            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[2, 3, 5])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=False)
            game_manager.update_game(game, sid='4', result=False)
            game_manager.update_game(game, sid='5', result=False)
            game_manager.update_game(game, sid='6', result=False)
            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[2, 3, 4])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='4', result=True)
            game_manager.update_game(game, sid='5', result=False)
            game_manager.update_game(game, sid='6', result=False)

            game_manager.update_game(game, sid='2', result=False)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='4', result=True)

            # 3
            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[1, 2, 3, 4])
            game_manager.update_game(game, sid='1', result=False)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='4', result=True)
            game_manager.update_game(game, sid='5', result=True)
            game_manager.update_game(game, sid='6', result=False)

            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='4', result=True)

            # 4
            # import json
            # print(json.dumps(game.to_dict()))
            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[1, 3, 4])
            game_manager.update_game(game, sid='1', result=False)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='4', result=True)
            game_manager.update_game(game, sid='5', result=True)
            game_manager.update_game(game, sid='6', result=False)

            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='3', result=True)
            game_manager.update_game(game, sid='4', result=True)

            self.assertTrue(game.stage == model.GameStage.finished)
            self.assertTrue(game.resistance_won is True)

    def test_multiple_games(self):

        self.test_game_complete_resistance_won_success()

        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            game = game_manager.new_game(game, sid=game.host.sid)

            self.game_id = game.id
            self.assertEqual(game.stage, model.GameStage.pending)
            game_manager.update_game(game, sid='1')
            self.assertEqual(game.stage, model.GameStage.executing_mission)
            game_manager.leave_game(game.id, '6', 6)
            game_manager.join_game(game, 'new', '6')
            self.assertEqual(game.stage, model.GameStage.pending)

            game_manager.update_game(game, sid='1')

            self.assertEqual(len(db.session.query(model.Game.id).all()), 2)
            self.assertEqual(len(db.session.query(model.Player.id).all()), 6)
            self.assertTrue(len(game.players), 6)

        self.test_game_complete_resistance_won_success()

        with self.app.app_context():
            self.assertEqual(len(db.session.query(model.Game.id).all()), 2)
            self.assertEqual(len(db.session.query(model.Player.id).all()), 6)
            self.assertTrue(len(game.players), 6)
