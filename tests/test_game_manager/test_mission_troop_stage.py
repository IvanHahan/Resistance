import errors
import model
from unittest import TestCase
from app import create_app, db, game_manager
import numpy as np
np.random.seed(13)


class TestMissionTroopStage(TestCase):
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

    def test_mission_started_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            self.assertTrue(mission.stage == model.RoundStage.troop_proposal)

    def test_troop_proposal_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            self.assertTrue(mission.stage == model.RoundStage.troop_voting)
            self.assertTrue(len(mission.current_voting().votes) == len(game.players))
            self.assertTrue(len(mission.troop_proposals[-1].members) == 1)
            self.assertTrue(mission.troop_proposals[-1].members[0].id == 1)

    def test_troop_proposal_not_leader_fail(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            with self.assertRaises(errors.NotLeader):
                game_manager.update_mission(mission, sid='-1', players_ids=[1])
            self.assertTrue(mission.stage == model.RoundStage.troop_proposal)

    def test_troop_proposal_wrong_troop_size_fail(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            with self.assertRaises(errors.InvalidPlayersNumber):
                game_manager.update_mission(game.current_mission(), sid=game.current_leader().sid, players_ids=[1, 2])
            self.assertTrue(game.current_mission().stage == model.RoundStage.troop_proposal)

    def test_troop_vote_approve_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_mission(mission, sid='1', result=True)
            game_manager.update_mission(mission, sid='2', result=True)
            game_manager.update_mission(mission, sid='3', result=True)
            self.assertTrue(mission.stage == model.RoundStage.mission_voting)
            self.assertTrue(mission.troop_proposals[-1].voting.result is True)

    def test_troop_vote_approve_twice_vote_fail(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_mission(mission, sid='1', result=True)
            game_manager.update_mission(mission, sid='2', result=True)
            with self.assertRaises(errors.CantVote):
                game_manager.update_mission(mission, sid='2', result=True)
            self.assertTrue(mission.stage == model.RoundStage.troop_voting)
            self.assertTrue(mission.troop_proposals[-1].voting.result is None)

    def test_troop_vote_disapprove_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            game_leader_sid = game.current_leader().sid
            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_mission(mission, sid='1', result=True)
            game_manager.update_mission(mission, sid='2', result=False)
            game_manager.update_mission(mission, sid='3', result=False)
            self.assertTrue(mission.stage == model.RoundStage.troop_proposal)
            self.assertTrue(mission.troop_proposals[-1].voting.result is False)
            self.assertTrue(game.current_leader().sid != game_leader_sid)

    def test_troop_vote_disapprove_mission_lose_success(self):
        with self.app.app_context():
            game = game_manager.request_game(self.game_id)
            mission = game.current_mission()
            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_mission(mission, sid='1', result=True)
            game_manager.update_mission(mission, sid='2', result=False)
            game_manager.update_mission(mission, sid='3', result=False)

            game_manager.update_mission(mission, sid=game.current_leader().sid, players_ids=[1])
            game_manager.update_mission(mission, sid='1', result=True)
            game_manager.update_mission(mission, sid='2', result=False)
            game_manager.update_mission(mission, sid='3', result=False)

            self.assertTrue(mission.stage == model.RoundStage.mission_results)
            self.assertTrue(mission.resistance_won is False)


class TestMissionTroopStageOnInterruptedGame(TestMissionTroopStage):

    def setUp(self):
        self.app = create_app('config.Test')
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            game_manager.leave_game(game.id, '2', 2)
            game_manager.join_game(game, 'test1', '2')
            game_manager.update_game(game, sid='1')
            self.game_id = game.id


class TestMissionTroopStageOnNewGame(TestMissionTroopStage):

    def setUp(self):
        self.app = create_app('config.Test')
        with self.app.app_context():
            game = game_manager.create_game('test', '1')
            game_manager.join_game(game, 'test1', '2')
            game_manager.join_game(game, 'test2', '3')
            game_manager.update_game(game, sid='1')
            game = game_manager.new_game(game, sid='1')
            game_manager.update_game(game, sid='1')
            self.game_id = game.id

    def tearDown(self):
        with self.app.app_context():
            self.assertEqual(len(db.session.query(model.Game.id).all()), 2)
        super().tearDown()