import enum

import numpy as np
from flask_socketio import emit

from app import db


class GameStatus(enum.Enum):
    pending = 0
    start_mission = 1
    end_mission = 2
    finished = 3


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    _status = db.Column(db.Enum(GameStatus), default=GameStatus.pending, nullable=False)
    resistance_won = db.Column(db.Boolean, nullable=True)
    missions_to_win = db.Column(db.Integer, default=1, nullable=False) #todo: change to 3
    _leader_idx = db.Column(db.Integer, nullable=False, default=-1)

    host_id = db.Column(db.Integer, db.ForeignKey('players.id', use_alter=True, name='fk_host_id'), nullable=True)

    host = db.relationship('Player', uselist=False, foreign_keys=[host_id], post_update=True)
    players = db.relationship('Player', uselist=True, back_populates='game', cascade='all, delete-orphan',
                              foreign_keys='[Player.game_id]')
    missions = db.relationship('Mission', back_populates='game', cascade='all, delete-orphan')

    def _set_status(self, status):
        self.status = status
        db.session.commit()

    def _new_mission(self):
        mission = Mission(game=self)
        db.session.add(mission)
        db.session.commit()
        return mission

    def _complete_game(self):
        fail_missions = len([mission for mission in self.missions if mission.voting.result is False])
        success_missions = len([mission for mission in self.missions if mission.voting.result is True])
        if fail_missions == self.missions_to_win:
            self.resistance_won = False
            return True
        elif success_missions == self.missions_to_win:
            self.resistance_won = True
            return True
        return False

    def current_mission(self):
        return self.missions[-1]

    def next_leader(self):
        if self._leader_idx == len(self.players) - 1:
            self._leader_idx = 0
        else:
            self._leader_idx += 1
        leader = self.players[self._leader_idx]
        return leader

    def current_leader(self):
        return self.players[self._leader_idx]

    def update(self):
        if self.status == GameStatus.pending:
            self.next()
        if self.status == GameStatus.start_mission:
            mission = self._new_mission()
            mission.update()
        if self.status == GameStatus.end_mission:
            if self._complete_game():
                self.next()
                emit('game_complete', self.resistance_won)
            else:
                self._set_status(GameStatus.start_mission)
                self.update()

    def next(self):
        self._set_status(GameStatus(self._status.value + 1))
        self.update()


class RoundStage(enum.Enum):
    proposal_request = 1
    troop_proposal = 2
    troop_voting = 3
    mission_voting = 4
    mission_results = 5


player_mission_association = db.Table('player_mission', db.metadata,
                                      db.Column('player_id', db.Integer, db.ForeignKey('players.id'), nullable=False),
                                      db.Column('mission_id', db.Integer, db.ForeignKey('missions.id'), nullable=False),
                                      )

player_proposal_association = db.Table('player_proposal', db.metadata,
                                       db.Column('player_id', db.Integer, db.ForeignKey('players.id'), nullable=False),
                                       db.Column('troop_proposal_id', db.Integer, db.ForeignKey('troop_proposals.id'),
                                                 nullable=False),
                                       )


class Mission(db.Model):
    __tablename__ = 'missions'

    id = db.Column(db.Integer, primary_key=True)
    _stage = db.Column(db.Enum(RoundStage), default=RoundStage.proposal_request, nullable=False)

    voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)

    voting = db.relationship('Voting', uselist=False, foreign_keys=[voting_id], cascade='all, delete-orphan', single_parent=True)
    troop_proposals = db.relationship('TroopProposal', uselist=True, cascade='all, delete-orphan')
    troop_members = db.relationship('Player', uselist=True, secondary=player_mission_association)
    game = db.relationship('Game', uselist=False, foreign_keys=[game_id], back_populates='missions')

    def _set_status(self, status):
        self._stage = status
        db.session.commit()

    def _new_troop_proposal(self, player_ids):
        players = db.session.query(Player).filter(Player.id.in_(player_ids)).all()
        voting = Voting()
        voting.votes = [Vote(voter=player) for player in players]
        proposal = TroopProposal(members=players,
                                 proposer=self.game.current_leader(),
                                 mission=self,
                                 voting=voting)
        db.session.add(proposal)
        db.session.add(voting)
        db.session.commit()
        return proposal

    def next(self, *args):
        self._set_status(RoundStage(self._stage.value + 1))
        self.update(*args)

    def update(self, *args):
        if self._stage == RoundStage.proposal_request:
            emit('query_proposal', (self.game.next_leader().id, self.to_dict()), room=self.game.id)

        elif self._stage == RoundStage.troop_proposal:
            player_ids = args[0]
            proposal = self._new_troop_proposal(player_ids)
            emit('start_voting', {'voting_id': proposal.voting_id,
                                  'candidates': player_ids,
                                  'voters': [player.id for player in self.game.players]}, room=self.game.id)

        elif self._stage == RoundStage.troop_voting:
            voting = self.troop_proposals[-1].voting
            voting.result = sum([v.result for v in voting.voting.votes]) > len(voting.voting.votes) // 2
            if voting.result:
                self.troop_members = self.troop_proposals[-1].members
                db.session.commit()
                emit('start_voting', [player.id for player in self.troop_members.members], room=self.game.id)
            else:
                self._set_status(RoundStage.proposal_request)
                self.update()

        elif self._stage == RoundStage.mission_voting:
            voting = self.voting
            voting.result = np.bitwise_or.reduce([vote.result for vote in voting.votes])
            self.next()
        elif self._stage == RoundStage.mission_results:
            self.game.next()
            emit('mission_complete', self.voting.result, room=self.game.id)

    def to_dict(self):
        return {
            'id': self.id,
            'stage': self._stage,
        }


class Role(enum.Enum):
    resistance = 0
    spy = 1


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    role = db.Column(db.Enum(Role), nullable=True)

    game_id = db.Column(db.Integer, db.ForeignKey('games.id', name='fk_game_id'), nullable=False)
    game = db.relationship('Game', uselist=False, back_populates='players', foreign_keys=[game_id])


class TroopProposal(db.Model):
    __tablename__ = 'troop_proposals'

    id = db.Column(db.Integer, primary_key=True)

    proposer_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=True)
    mission_id = db.Column(db.Integer, db.ForeignKey('missions.id'), nullable=False)

    members = db.relationship('Player', uselist=True, secondary=player_proposal_association)
    proposer = db.relationship('Player', uselist=False)
    voting = db.relationship('Voting', uselist=False, cascade='all, delete-orphan', single_parent=True)
    mission = db.relationship('Mission', uselist=False)


class Voting(db.Model):
    __tablename__ = 'votings'

    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.Boolean, nullable=True)

    votes = db.relationship('Vote', uselist=True, back_populates='voting', cascade='all, delete-orphan')

    def vote(self, player_id, result):
        vote = [vote for vote in self.votes if vote.voter_id == player_id][0]
        vote.result = result

        vote_complete = np.bitwise_and.reduce([vote.result is not None for vote in self.votes])
        mission = db.session.query(Player).filter(Player.id == player_id).first().game.current_mission()  # TODO: rewrite
        if vote_complete:
            mission.next()
        else:
            return


class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.Boolean, nullable=True)

    voter_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=False)

    voter = db.relationship('Player', uselist=False)
    voting = db.relationship('Voting', uselist=False, back_populates='votes')
