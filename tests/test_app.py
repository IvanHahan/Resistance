from unittest import TestCase

from app import create_app, socketio, db
from flask import current_app as app
import model


class TestGame(TestCase):

    def setUp(self):
        self.app = create_app('config.Test')

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_simulate_game(self):
        clients = [socketio.test_client(self.app) for _ in range(5)]
        host = clients[0]
        host.connect()
        host.emit('create_game', 'Ivan')
        recieved = host.get_received()
        assert recieved[0]['args'] == 'joined_game'
        with self.app.app_context():
            assert len(db.session.query(model.Player).all()) == 1
            assert len(db.session.query(model.Game).all()) == 1


