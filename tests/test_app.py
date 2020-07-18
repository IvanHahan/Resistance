from unittest import TestCase

from app import create_app, socketio, db
import app
# from flask import current_app as app
from model import model


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
        host_id = received[1]['args'][0]['host_id']
        game_id = received[1]['args'][0]['id']
        assert host_id is not None

        clients = [socketio.test_client(self.app) for _ in range(2)]

        player_ids = []
        for i, client in enumerate(clients):
            client.emit('join_game', str(i), 1)
            received = client.get_received()
            assert received[1]['name'] == 'player_joined'
            player_ids.append(received[1]['args'][0]['id'])

        with self.app.app_context():
            assert len(db.session.query(model.Player).all()) == 3
            assert len(db.session.query(model.Game).all()) == 1
            assert len(db.session.query(model.Game.players).filter(model.Game.id == 1).all()) == 3

        for client in [host_client, *clients]:
            received = client.get_received()

        host_client.emit('start_game', host_id)
        proposer_client = None
        for client, id in zip([host_client, *clients], [host_id, *player_ids]):
            received = client.get_received()
            data = received[0]['args'][0]
            if data['leader_id'] == id:
                target_players = data['target_players']
                assert target_players == app.rules[3]['mission_team'][0]
                assert id == host_id
                proposer_client = client

        proposer_client.emit('make_proposal', {'game_id': game_id, 'players_id': (1, )})

        for client, id in zip([host_client, *clients], [host_id, *player_ids]):
            received = client.get_received()
            data = received[0]['args'][0]
            if id in data['voters']:
                client.emit('vote', {'voting_id': data['voting_id'], 'result': True, 'voter_id': id})

        for client, id in zip([host_client, *clients], [host_id, *player_ids]):
            received = client.get_received()
            data = [t for t in received if t['name'] == 'start_voting'][0]['args'][0]
            if id in data['voters']:
                client.emit('vote', {'voting_id': data['voting_id'], 'result': True, 'voter_id': id})
            else:
                assert len([t for t in received if t['name'] == 'game_complete']) == 1

        received = host_client.get_received()
        assert len([t for t in received if t['name'] == 'game_complete']) == 1

