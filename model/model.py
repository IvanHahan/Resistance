import enum

import numpy as np

from app import db
from flask_login import UserMixin


player_game_association = db.Table('player_game', db.metadata,
                                       db.Column('player_id', db.Integer, db.ForeignKey('players.id', ondelete='cascade'), nullable=False),
                                       db.Column('game_id', db.Integer, db.ForeignKey('games.id', ondelete='cascade'),
                                                 nullable=False),
                                       )


player_mission_association = db.Table('player_mission', db.metadata,
                                      db.Column('player_id', db.Integer,
                                                db.ForeignKey('players.id', ondelete='cascade'),
                                                nullable=False),
                                      db.Column('mission_id', db.Integer,
                                                db.ForeignKey('missions.id', ondelete='cascade'),
                                                nullable=False),
                                      )

player_proposal_association = db.Table('player_proposal', db.metadata,
                                       db.Column('player_id', db.Integer,
                                                 db.ForeignKey('players.id', ondelete='cascade'),
                                                 nullable=False),
                                       db.Column('troop_proposal_id', db.Integer, db.ForeignKey('troop_proposals.id', ondelete='cascade'),
                                                 nullable=False),
                                       )


class Role(enum.Enum):
    resistance = 0
    spy = 1


class Player(db.Model):
    __tablename__ = 'players'
    __table_args__ = (
        db.UniqueConstraint('name', 'game_id', name='unique_name_game'),
        db.UniqueConstraint('sid', 'game_id', name='unique_sid_game'),
    )

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Enum(Role), nullable=True)
    sid = db.Column(db.String, nullable=False, unique=False)
    name = db.Column(db.String, nullable=False, unique=False)

    game_id = db.Column(db.Integer, db.ForeignKey('games.id', name='fk_game_id', ondelete='cascade'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'), nullable=False)
    user = db.relationship('User', uselist=False)
    game = db.relationship('Game', uselist=False, foreign_keys=[game_id])
    games = db.relationship('Game', uselist=True, secondary=player_game_association, back_populates='players',
                            cascade='all, delete')

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role.name if self.role is not None else None,
            'game_id': self.game_id,
            'name': self.name
        }

    def __repr__(self):
        return f'Player {self.id}, {self.sid}'


class TroopProposal(db.Model):
    __tablename__ = 'troop_proposals'

    id = db.Column(db.Integer, primary_key=True)

    proposer_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=True)
    mission_id = db.Column(db.Integer, db.ForeignKey('missions.id'), nullable=False)

    members = db.relationship('Player', uselist=True, secondary=player_proposal_association)
    proposer = db.relationship('Player', uselist=False)
    voting = db.relationship('Voting', uselist=False, cascade='all, delete', single_parent=True)
    mission = db.relationship('Mission', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'proposer_id': self.proposer.id,
            'voting': self.voting.to_dict() if self.voting is not None else None,
            'mission_id': self.mission_id,
            'members_ids': [p.id for p in self.members],
        }


class Voting(db.Model):
    __tablename__ = 'votings'

    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.Boolean, nullable=True)

    votes = db.relationship('Vote', uselist=True, back_populates='voting', cascade='all, delete')

    def is_complete(self):
        return np.bitwise_and.reduce([vote.result is not None for vote in self.votes])

    def vote(self, player_id, result):
        vote = [vote for vote in self.votes if vote.voter_id == player_id][0]
        vote.result = result

    def to_dict(self):
        return {
            'id': self.id,
            'result': self.result,
            'votes': [v.to_dict() for v in self.votes],
        }


class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.Boolean, nullable=True, default=None)

    voter_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=False)

    voter = db.relationship('Player', uselist=False)
    voting = db.relationship('Voting', uselist=False, back_populates='votes')

    def to_dict(self):
        return {
            'id': self.id,
            'result': self.result,
            'voter_id': self.voter_id,
            'voting_id': self.voting_id
        }

    def __repr__(self):
        return f'Vote {self.id}, {self.result}'
