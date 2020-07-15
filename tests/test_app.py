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
        host_client = socketio.test_client(self.app)
        host_client.emit('create_game', 'Ivan')
        received = host_client.get_received()
        host_id = received[1]['args'][0]
        assert host_id is not None

        clients = [socketio.test_client(self.app) for _ in range(4)]

        player_ids = []
        for i, client in enumerate(clients):
            client.emit('join_game', str(i), 1)
            received = client.get_received()
            assert received[0]['name'] == 'player_joined'
            assert received[0]['args'][0] is not None
            player_ids.append(received[0]['args'][0])

        with self.app.app_context():
            assert len(db.session.query(model.Player).all()) == 5
            assert len(db.session.query(model.Game).all()) == 1
            assert len(db.session.query(model.Game.players).filter(model.Game.id == 1).all()) == 5

        for client in [host_client, *clients]:
            received = client.get_received()

        host_client.emit('start_game', host_id)
        proposer_client = None
        mission_id = None
        for client, id in zip([host_client, *clients], [host_id, *player_ids]):
            received = client.get_received()
            leader_id, mission = received[0]['args']
            if leader_id == id:
                mission_id = mission['id']
                proposer_client = client

        proposer_client.emit('make_proposal', mission_id, (1, 2))

        for client, id in zip([host_client, *clients], [host_id, *player_ids]):
            received = client.get_received()
            data = received[0]['args'][0]
            if id in data['voters']:
                client.emit('vote', {'voting_id': data['voting_id'], 'result': True, 'voter_id': id})


