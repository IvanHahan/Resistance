from callbacks import socket_actions as actions
from .model import *
from app import db


class RoundStage(enum.Enum):
    proposal_request = 1
    troop_proposal = 2
    troop_voting = 3
    troop_voting_results = 4
    mission_voting = 5
    mission_voting_result = 6
    mission_results = 7


class Mission(db.Model):
    __tablename__ = 'missions'
    __table_args__ = (
        db.UniqueConstraint('index', 'game_id', name='unique_index_game'),
    )

    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, nullable=False, unique=False)
    _stage = db.Column(db.Enum(RoundStage), default=RoundStage.proposal_request, nullable=False)

    voting_id = db.Column(db.Integer, db.ForeignKey('votings.id'), nullable=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    num_of_fails = db.Column(db.Integer, default=1, nullable=False)

    voting = db.relationship('Voting', uselist=False, foreign_keys=[voting_id], cascade='all, delete-orphan',
                             single_parent=True)
    troop_proposals = db.relationship('TroopProposal', uselist=True, cascade='all, delete-orphan',
                                      order_by='TroopProposal.id')
    troop_members = db.relationship('Player', uselist=True, secondary=player_mission_association)
    game = db.relationship('Game', uselist=False, foreign_keys=[game_id], back_populates='missions')

    @property
    def stage(self):
        return self._stage

    def next(self):
        self._stage = RoundStage(int(self.stage.value) + 1)
        return self.stage

    def _set_status(self, status):
        self._stage = status
        db.session.commit()

    def _new_troop_proposal(self, player_ids):
        players = db.session.query(Player).filter(Player.id.in_(player_ids)).all()
        voting = Voting()
        voting.votes = [Vote(voter=player) for player in self.game.players]
        proposal = TroopProposal(members=players,
                                 proposer=self.game.current_leader(),
                                 mission=self,
                                 voting=voting)
        db.session.add(proposal)
        db.session.add(voting)
        db.session.commit()
        return proposal

    def update(self, **kwargs):
        return self.update_for_state(self._stage, **kwargs)

    def update_for_state(self, state, **kwargs):

        self._set_status(state)
        if self._stage == RoundStage.proposal_request:
            target_players = app.rules[len(self.game.players)]['mission_team'][len(self.game.missions) - 1]
            return actions.MissionUpdated(self.game_id, self.to_dict())
            # return actions.QueryProposal(self.game_id, self.game.next_leader().id, target_players)

        elif self._stage == RoundStage.troop_proposal:
            target_players = app.rules[len(self.game.players)]['mission_team'][len(self.game.missions) - 1]

            if 'players_ids' not in kwargs:
                raise errors.InvalidPlayersNumber(0, target_players)

            player_ids = kwargs['players_ids']
            if len(player_ids) != target_players:
                raise errors.InvalidPlayersNumber(len(player_ids), target_players)

            proposal = self._new_troop_proposal(player_ids)
            return actions.MissionUpdated(self.game_id, self.to_dict())
            # return actions.StartVoting(self.game_id, player_ids,
            #                            [player.id for player in self.game.players])

        elif self._stage == RoundStage.troop_voting:
            if 'result' not in kwargs and 'player_id' not in kwargs:
                return actions.MissionUpdated(self.game_id, self.to_dict())
                # return actions.StartVoting(self.game_id, [player.id for player in self.troop_proposals[-1].members],
                #                            [vote.voter_id for vote in self.current_voting().votes if
                #                             vote.result is None])
            self.current_voting().vote(kwargs['player_id'], kwargs['result'])
            if self.current_voting().is_complete():
                return self.update_for_state(RoundStage.troop_voting_results)
        elif self._stage == RoundStage.troop_voting_results:
            voting = self.troop_proposals[-1].voting
            voting.result = sum([v.result for v in voting.votes]) > len(voting.votes) // 2
            if voting.result:
                self.troop_members = self.troop_proposals[-1].members
                self.voting = Voting()
                self.voting.votes = [Vote(voter=player) for player in self.troop_members]
                db.session.add(self.voting)
                db.session.commit()
                return actions.MissionUpdated(self.game_id, self.to_dict())
                # return actions.StartVoting(self.game_id, None,
                #                            [player.id for player in self.troop_members])

            else:
                return self.update_for_state(RoundStage.proposal_request)
        elif self._stage == RoundStage.mission_voting:
            if 'result' not in kwargs and 'player_id' not in kwargs:
                return actions.MissionUpdated(self.game_id, self.to_dict())
                # return actions.StartVoting(self.game_id, None,
                #                            [vote.voter_id for vote in self.current_voting().votes if
                #                             vote.result is None])
            self.current_voting().vote(kwargs['player_id'], kwargs['result'])
            if self.current_voting().is_complete():
                return self.update_for_state(RoundStage.mission_voting_result)
        elif self._stage == RoundStage.mission_voting_result:
            voting = self.voting
            voting.result = np.bitwise_not([vote.result for vote in voting.votes]).sum() < self.num_of_fails
            return self.update_for_state(RoundStage.mission_results)

        elif self._stage == RoundStage.mission_results:
            return actions.MissionUpdated(self.game_id, self.to_dict())
            # return actions.MissionComplete(self.game_id, self.voting.result)

    def current_voting(self):
        if self.voting is not None:
            return self.voting
        elif len(self.troop_proposals) > 0:
            return self.troop_proposals[-1].voting
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'index': self.index,
            'stage': self.stage.name,
            'game_id': self.game_id,
            'proposals': [tp.to_dict() for tp in self.troop_proposals],
            'voting': self.voting.to_dict() if self.voting is not None else None
        }

    def __repr__(self):
        return f'Mission {self.id} {self.stage}'