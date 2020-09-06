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
            with self.assertRaises(errors.GameFull):
                game_manager.join_game(game, 'test3', '4')

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
                game_manager.update_mission(mission, sid='2', players_ids=[1])
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



