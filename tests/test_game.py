from unittest import TestCase

import errors
import model
from callbacks import socket_actions as actions
from app import create_app, db


class TestGameStart(TestCase):

    def setUp(self):
        self.app = create_app('config.Test')

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_game_start_insufficient_players(self):
        with self.app.app_context():
            game = model.Game()
            game.add_player('1', True)
            game.add_player('2')
            db.session.add(game)
            db.session.commit()
            with self.assertRaises(errors.InsufficientPlayersNumber):
                game.update()

    def test_game_start_sufficient_players(self):
        with self.app.app_context():
            game = model.Game()
            p1 = game.add_player('1', True)
            p2 = game.add_player('2')
            p3 = game.add_player('3')
            db.session.add(game)
            db.session.commit()
            game.update()
            self.assertTrue(p1.role is not None)
            self.assertTrue(p2.role is not None)
            self.assertTrue(p3.role is not None)


class TestGameMiddle(TestCase):
    def setUp(self):
        self.app = create_app('config.Test')
        with self.app.app_context():
            game = model.Game()
            p1 = game.add_player('1', True)
            p2 = game.add_player('2')
            p3 = game.add_player('3')
            db.session.add(game)
            db.session.commit()
            self.game_id = game.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_game_failed_troop_voting(self):
        with self.app.app_context():
            game = db.session.query(model.Game).filter(model.Game.id == self.game_id).first()
            actions_ = game.update()
            self.assertTrue(isinstance(actions_[0], actions.QueryProposal))
            self.assertTrue(game.status == model.GameStage.executing_mission)
            actions_ = game.update(model.RoundStage.troop_proposal, players_ids=(1,))
            self.assertTrue(isinstance(actions_[0], actions.StartVoting))
            for p in game.players:
                actions_ = game.update(model.RoundStage.troop_voting, result=False, player_id=p.id)
            self.assertTrue(isinstance(actions_[0], actions.QueryProposal))
            self.assertTrue(game._leader_idx == 1)

    def test_game_pause_resume_failed_troop_voting(self):
        with self.app.app_context():
            game = db.session.query(model.Game).filter(model.Game.id == self.game_id).first()
            actions_ = game.update()
            self.assertTrue(isinstance(actions_[0], actions.QueryProposal))
            self.assertTrue(game.status == model.GameStage.executing_mission)
            actions_ = game.update(model.RoundStage.troop_proposal, players_ids=(1,))
            self.assertTrue(isinstance(actions_[0], actions.StartVoting))
            game.pause()
            for p in game.players:
                actions_ = game.update(model.RoundStage.troop_voting, result=False, player_id=p.id)
                self.assertTrue(isinstance(actions_[0], actions.GamePaused))
            game.resume()
            for p in game.players:
                actions_ = game.update(model.RoundStage.troop_voting, result=False, player_id=p.id)
            self.assertTrue(isinstance(actions_[0], actions.QueryProposal))

    def test_simulate_game_success(self):
        with self.app.app_context():
            game = db.session.query(model.Game).filter(model.Game.id == self.game_id).first()
            actions_ = game.update()
            self.assertTrue(isinstance(actions_[0], actions.QueryProposal))
            self.assertTrue(game.status == model.GameStage.executing_mission)
            actions_ = game.update(model.RoundStage.troop_proposal, players_ids=(1,))
            self.assertTrue(isinstance(actions_[0], actions.StartVoting))
            for p in game.players:
                actions_ = game.update(model.RoundStage.troop_voting, result=True, player_id=p.id)
            self.assertTrue(isinstance(actions_[0], actions.StartVoting))
            actions_ = game.update(model.RoundStage.mission_voting, result=True, player_id=game.players[0].id)
            self.assertTrue(isinstance(actions_[0], actions.MissionComplete))
            self.assertTrue(game.resistance_won is not None)
