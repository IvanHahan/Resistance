import enum

from app import db


class GameStatus(enum.Enum):
    pending = 0
    ongoing = 1
    finished = 2


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(GameStatus), default=GameStatus.pending, nullable=False)
    resistance_won = db.Column(db.Boolean, nullable=True)

    leader_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    host_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)

    host = db.relationship('Player', uselist=False)
    leader = db.relationship('Player', uselist=False)
    players = db.relationship('Player', backpopulates='game', cascade='all, delete-orphan')
    rounds = db.relationship('Mission', backpopulates='game', cascade='all, delete-orphan')


class RoundStage(enum.Enum):
    troop_proposal = 0
    troop_voting = 1
    mission_voting = 2
    mission_results = 3


player_mission_association = db.Table('player_mission', db.metadata,
                          db.Column('player_id', db.Integer, db.ForeignKey('players.id')),
                          db.Column('mission_id', db.Integer, db.ForeignKey('missions.id')),
                          )

player_proposal_association = db.Table('player_proposal', db.metadata,
                          db.Column('player_id', db.Integer, db.ForeignKey('players.id')),
                          db.Column('troop_proposal_id', db.Integer, db.ForeignKey('troop_proposals.id')),
                          )


class Mission(db.Model):
    __tablename__ = 'missions'

    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.Boolean, nullable=True)
    stage = db.Column(db.Enum(RoundStage), default=RoundStage.troop_proposal, nullable=False)

    mission_voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=True)

    mission_voting = db.relationship('Voting', uselist=False)
    troop_proposals = db.relationship('TroopProposal', uselist=True)
    troop_members = db.relationship('Player', uselist=True, secondary=player_mission_association)


class Role(enum.Enum):
    resistance = 0
    spy = 1


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.Enum(Role), nullable=True)

    game_id = db.Column(db.Integer, db.ForeignKey('Game.id'), nullable=False)
