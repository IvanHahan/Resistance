import enum

from __main__ import db


class GameStatus(enum.Enum):
    pending = 0
    start_mission = 1
    end_mission = 2
    finished = 3


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(GameStatus), default=GameStatus.pending, nullable=False)
    resistance_won = db.Column(db.Boolean, nullable=True)
    leader_idx = db.Column(db.Integer, nullable=False, default=-1)

    host_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)

    host = db.relationship('Player', uselist=False, foreign_keys=[host_id], post_update=True)
    players = db.relationship('Player', uselist=True, back_populates='game', cascade='all, delete-orphan',
                              foreign_keys='[Player.game_id]')
    missions = db.relationship('Mission', back_populates='game', cascade='all, delete-orphan')

    def start(self):
        self.status = GameStatus.start_mission


class RoundStage(enum.Enum):
    proposal_request = 0
    troop_proposal = 1
    troop_voting = 2
    mission_voting = 3
    mission_results = 4


player_mission_association = db.Table('player_mission', db.metadata,
                          db.Column('player_id', db.Integer, db.ForeignKey('players.id'), nullable=False),
                          db.Column('mission_id', db.Integer, db.ForeignKey('missions.id'), nullable=False),
                          )

player_proposal_association = db.Table('player_proposal', db.metadata,
                          db.Column('player_id', db.Integer, db.ForeignKey('players.id'), nullable=False),
                          db.Column('troop_proposal_id', db.Integer, db.ForeignKey('troop_proposals.id'), nullable=False),
                          )


class Mission(db.Model):
    __tablename__ = 'missions'

    id = db.Column(db.Integer, primary_key=True)
    stage = db.Column(db.Enum(RoundStage), default=RoundStage.troop_proposal, nullable=False)

    voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)

    voting = db.relationship('Voting', uselist=False, cascade='all, delete-orphan', single_parent=True)
    troop_proposals = db.relationship('TroopProposal', uselist=True, cascade='all, delete-orphan')
    troop_members = db.relationship('Player', uselist=True, secondary=player_mission_association)
    game = db.relationship('Game', uselist=False, back_populates='missions')


class Role(enum.Enum):
    resistance = 0
    spy = 1


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    role = db.Column(db.Enum(Role), nullable=True)

    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
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


class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.Boolean, nullable=True)

    voter_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=False)

    voter = db.relationship('Player', uselist=False)
    voting = db.relationship('Voting', uselist=False, back_populates='votes')

