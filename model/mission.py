from .model import *
import socket_actions as actions


class RoundStage(enum.Enum):
    proposal_request = 1
    troop_proposal = 2
    troop_voting = 3
    mission_voting = 4
    mission_results = 5


class Mission(db.Model):
    __tablename__ = 'missions'

    id = db.Column(db.Integer, primary_key=True)
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

    def next(self, *args):
        self._set_status(RoundStage(self._stage.value + 1))
        return self.update(*args)

    def update(self, *args):
        if self._stage == RoundStage.proposal_request:
            target_players = app.rules[len(self.game.players)]['mission_team'][len(self.game.missions) - 1]
            return actions.QueryProposal(self.game_id, self.game.next_leader().id, target_players)

        elif self._stage == RoundStage.troop_proposal:
            player_ids = args[0]
            target_players = app.rules[len(self.game.players)]['mission_team'][len(self.game.missions) - 1]
            if len(player_ids) != target_players:
                raise errors.InvalidPlayersNumber(len(player_ids), target_players)
            proposal = self._new_troop_proposal(player_ids)
            return actions.StartVoting(self.game_id, proposal.voting_id, player_ids,
                                       [player.id for player in self.game.players])

        elif self._stage == RoundStage.troop_voting:
            voting = self.troop_proposals[-1].voting
            voting.result = sum([v.result for v in voting.votes]) > len(voting.votes) // 2
            if voting.result:
                self.troop_members = self.troop_proposals[-1].members
                self.voting = Voting()
                self.voting.votes = [Vote(voter=player) for player in self.troop_members]
                db.session.add(self.voting)
                db.session.commit()
                return actions.StartVoting(self.game_id, self.voting_id, None,
                                           [player.id for player in self.troop_members])

            else:
                self._set_status(RoundStage.proposal_request)
                return self.update()

        elif self._stage == RoundStage.mission_voting:
            voting = self.voting
            voting.result = np.bitwise_not([vote.result for vote in voting.votes]).sum() < self.num_of_fails
            return self.next()

        elif self._stage == RoundStage.mission_results:
            return actions.MissionComplete(self.game_id, self.voting.result)

    def current_voting(self):
        if self._stage == RoundStage.troop_proposal:
            return self.troop_proposals[-1].voting
        elif self._stage == RoundStage.troop_voting:
            return self.voting

    def to_dict(self):
        return {
            'id': self.id,
            'stage': self._stage,
            'members_ids': [m.id for m in self.troop_members],
            'proposals': [p.to_dict() for p in self.troop_proposals],
            'game_id': self.game_id,
            'voting': self.voting.to_dict() if self.voting is not None else None,
        }
