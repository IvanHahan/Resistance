import errors
import model
from unittest import TestCase
from app import create_app, db, game_manager
import numpy as np
np.random.seed(13)


class TestMissionMissionStage(TestCase):
    def setUp(self):
        self.app = create_app('config.Test')
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            mission = game.current_mission()
            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_mission(mission, sid='1', result=True)
            game_manager.update_mission(mission, sid='2', result=True)
            game_manager.update_mission(mission, sid='3', result=True)
            self.game_id = game.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_mission_vote_approve_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            game_manager.update_mission(mission, sid='1', result=True)
            self.assertTrue(mission.stage == model.RoundStage.mission_results)
            self.assertTrue(mission.voting.result is True)

    def test_mission_vote_disapprove_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            game_manager.update_mission(mission, sid='1', result=False)
            self.assertTrue(mission.stage == model.RoundStage.mission_results)
            self.assertTrue(mission.voting.result is False)

    def test_mission_vote_approve_wrong_user_fail(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            with self.assertRaises(errors.CantVote):
                game_manager.update_mission(mission, sid='2', result=True)
            self.assertTrue(mission.stage == model.RoundStage.mission_voting)
            self.assertTrue(mission.voting.result is None)


class TestMissionMissionStageOnInterruptedGame(TestMissionMissionStage):

    def setUp(self):
        self.app = create_app('config.Test')
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            mission = game.current_mission()
            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_mission(mission, sid='1', result=True)
            game_manager.update_mission(mission, sid='2', result=True)
            game_manager.update_mission(mission, sid='3', result=True)

            game_manager.leave_game(game.id, '2', 2)
            game_manager.join_game(game, 'test1', '2')
            game_manager.update_game(game, sid='1')

            mission = game.current_mission()
            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_mission(mission, sid='1', result=True)
            game_manager.update_mission(mission, sid='2', result=True)
            game_manager.update_mission(mission, sid='3', result=True)

            self.game_id = game.id


class TestSubsequentMissionStage(TestCase):
    def setUp(self):
        self.app = create_app('config.Test')
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')

            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)

            game_manager.update_game(game, sid='1', result=True)
            self.game_id = game.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_next_mission_troop_fail_then_success_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            current_mission_id = game.current_mission().id
            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[1, 2])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=False)
            game_manager.update_game(game, sid='3', result=False)
            self.assertTrue(game.current_mission().stage == model.RoundStage.troop_proposal)
            game_manager.update_game(game, sid=game.current_leader().sid, players_ids=[2, 3])
            game_manager.update_game(game, sid='1', result=True)
            game_manager.update_game(game, sid='2', result=True)
            game_manager.update_game(game, sid='3', result=True)
            self.assertTrue(game.current_mission().id == current_mission_id)
            self.assertTrue(game.current_mission().stage == model.RoundStage.mission_voting)