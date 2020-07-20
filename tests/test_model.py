from unittest import TestCase

import errors
import model
import socket_actions as actions
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
            self.assertTrue(player1.role is not None)
            self.assertTrue(player2.role is not None)
            self.assertTrue(player3.role is not None)


class TestGameMiddle(TestCase):
    def setUp(self):
        self.app = create_app('config.Test')
        with self.app.app_context():
            game = model.Game()
            player1 = model.Player(name='1', game=game)
            player2 = model.Player(name='2', game=game)
            player3 = model.Player(name='3', game=game)
            game.host = player1
            db.session.add(game)
            db.session.commit()
            self.game_id = game.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_game_failed_troop_voting(self):
        with self.app.app_context():
            game = db.session.query(model.Game).filter(model.Game.id == self.game_id).first()
            actions_ = game.next()
            self.assertTrue(isinstance(actions_[0], actions.QueryProposal))
            self.assertTrue(game.status == model.GameStatus.executing_mission)
            action = game.current_mission().next((1,))
            self.assertTrue(isinstance(action, actions.StartVoting))
            voting = game.current_mission().troop_proposals[-1].voting
            for p in game.players:
                action = voting.vote(p.id, False)
            self.assertTrue(action is not None)
            self.assertTrue(isinstance(action, actions.QueryProposal))
            self.assertTrue(game._leader_idx == 1)
