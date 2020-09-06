import numpy as np
from sqlalchemy.exc import IntegrityError

import errors
import model
from app import db
from callbacks import socket_actions as actions


def db_commit(function):
    def func(*args, **kwargs):
        try:
            result = function(*args, **kwargs)
            db.session.commit()
            return result
        except IntegrityError as err:
            print(err)
            db.session.rollback()
            raise errors.ForbiddenAction()

    return func


class GameManager:

    # Getters

    def configure(self, rules):
        self.min_players = min(rules['team'].keys())
        self.max_players = max(rules['team'].keys())
        self.rules = rules
        model.Game.missions_to_win = rules['missions_to_win']

    def request_game(self, id):
        game = db.session.query(model.Game).filter(model.Game.id == id).first()
        if game is None:
            raise errors.GameNotFound()
        return game

    def request_mission(self, id):
        return db.session.query(model.Mission).filter(model.Mission.id == id).first()

    def request_games(self):
        return db.session.query(model.Game).filter(model.Game.stage == model.GameStage.pending).all()

    def request_player(self, id):
        player = db.session.query(model.Player).filter(model.Player.id == id).first()
        if player is None:
            raise errors.UknownPlayer()
        return player

    def request_player_with_sid(self, sid, game_id):
        player = db.session.query(model.Player).filter(db.and_(model.Player.sid == sid,
                                                               model.Player.game_id == game_id)).first()
        if player is None:
            raise errors.UknownPlayer()
        return player

    @db_commit
    def activate_player(self, player):
        player.active = True

    @db_commit
    def deactivate_player(self, player):
        player.active = False

    @db_commit
    def update_player_sid(self, old_sid, sid):
        player = db.session.query(model.Player).filter(model.Player.sid == old_sid).first()
        if player is not None:
            player.sid = sid

    # Setters

    @db_commit
    def create_game(self, host_name, sid):
        game = model.Game()
        player = model.Player(name=host_name, sid=sid, game=game)
        player.games.append(game)
        game.host = player
        db.session.add(game)
        db.session.add(player)

        return game

    @db_commit
    def new_game(self, game_, **kwargs):
        if game_.host.sid != kwargs['sid']:
            raise errors.ForbiddenAction()

        game = model.Game()
        db.session.add(game)

        for p in game_.players:
            p.game = game
            p.games.append(game)
        game.host_id = game_.host.id

        return game

    @db_commit
    def join_game(self, game, name, sid):
        game_stage = db.session.query(model.Game.stage).filter(db.and_(model.Game.id == game.id)).first()
        if game_stage is None:
            raise errors.GameNotFound()
        elif game_stage[0] != model.GameStage.pending:
            raise errors.ForbiddenAction()
        elif len(db.session.query(model.Player.id).filter(model.Player.game_id == game.id).all()) == self.max_players:
            raise errors.GameFull()
        player = model.Player(name=name, sid=sid, game_id=game.id)
        player.games.append(game)
        db.session.add(player)
        return player

    @db_commit
    def leave_game(self, game_id, sid, player_id):

        player = db.session.query(model.Player).filter(db.and_(model.Player.sid == sid,
                                                               model.Player.game_id == game_id)).first()
        if player is None:
            raise errors.UknownPlayer()
        # Player wants to leave
        if player.id == player_id:

            db.session.query(model.Player).filter(db.and_(model.Player.sid == sid,
                                                          model.Player.game_id == game_id)).delete()
            db.session.query(model.Game).filter(model.Game.host_id == player.id).delete()

        # Player wants to kick
        elif db.session.query(model.Game).filter(db.and_(model.Game.host_id == player.id,
                                                         model.Game.id == game_id)).first() is not None:
            db.session.query(model.Player).filter(db.and_(model.Player.id == player_id,
                                                          model.Player.game_id == game_id)).delete()
        else:
            raise errors.ForbiddenAction()

        game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
        if game is not None and game.stage != model.GameStage.pending:
            self.reset_game(game)

    def is_host(self, game_id, sid):
        player_id = db.session.query(model.Player.id).filter(db.and_(model.Player.sid == sid,
                                                                     model.Player.game_id == game_id)).first()
        if player_id is None:
            raise errors.UknownPlayer()
        elif db.session.query(model.Game).filter(db.and_(model.Game.host_id == player_id[0],
                                                         model.Game.id == game_id)).first() is None:
            return False
        return True

    def try_delete_game(self, game_id, sid):

        if self.is_host(game_id, sid):
            self.delete_game(game_id)
        else:
            raise errors.ForbiddenAction()

    @db_commit
    def delete_game(self, game_id):
        db.session.query(model.Game).filter(model.Game.id == game_id).delete()

    def is_game_active(self, game_id):
        return db.session.query(model.Player.id).filter(db.and_(model.Player.game_id == game_id,
                                                             model.Player.active == True)) > 0

    @db_commit
    def update_game(self, game, **kwargs):

        if game.stage == model.GameStage.pending:
            return self._handle_pending(game, **kwargs)
        if game.stage == model.GameStage.starting:
            return self._handle_starting(game, **kwargs)
        elif game.stage == model.GameStage.start_mission:
            return self._handle_start_mission(game, **kwargs)
        elif game.stage == model.GameStage.executing_mission:
            return self._handle_executing_mission(game, **kwargs)
        elif game.stage == model.GameStage.finished:
            raise errors.GameFinished()

    def reset_game(self, game):
        game.stage = model.GameStage.pending
        db.session.query(model.Mission).filter(model.Mission.game_id == game.id).delete()
        return actions.GameUpdated(game.to_dict(), game.host_id)

    def _handle_pending(self, game, **kwargs):
        if game.host.sid != kwargs['sid']:
            raise errors.ForbiddenAction()
        elif len(game.players) < self.min_players:
            raise errors.InsufficientPlayersNumber()

        game.next()
        db.session.commit()
        return self.update_game(game, **kwargs)

    def _handle_starting(self, game, **kwargs):
        game.setup(self.rules['team'][len(game.players)]['spies'])
        game.next()
        db.session.commit()
        return self.update_game(game, **kwargs)

    def _handle_start_mission(self, game, **kwargs):
        _ = self._create_mission(game.id, len(game.players), len(game.missions))
        game.next()
        db.session.commit()
        return self.update_game(game, **kwargs)

    def _handle_executing_mission(self, game, **kwargs):
        action = self.update_mission(game.current_mission(), **kwargs)
        if game.current_mission().stage == model.RoundStage.mission_results:
            if game._complete_game():
                game.next()
                db.session.commit()
                return actions.GameUpdated(game.to_dict(), game.host_id)
            else:
                game.stage = model.GameStage.start_mission
                db.session.commit()
                return self.update_game(game, **kwargs)
        return actions.GameUpdated(game.to_dict(), game.host_id)

    def _create_mission(self, game_id, num_players, index):
        mission = model.Mission(game_id=game_id, index=index,
                                num_of_fails=self.rules['team'][num_players]['fails_num'][index])
        db.session.add(mission)
        return mission

    def _create_proposal(self, mission_id, proposer_id, members_ids, players_ids):
        players = db.session.query(model.Player).filter(model.Player.id.in_(members_ids)).all()
        voting = model.Voting()
        voting.votes = [model.Vote(voter_id=player) for player in players_ids]
        proposal = model.TroopProposal(members=players,
                                       proposer_id=proposer_id,
                                       mission_id=mission_id,
                                       voting=voting)
        db.session.add(proposal)
        db.session.add(voting)
        return proposal

    @db_commit
    def update_mission(self, mission, **kwargs):
        if mission.stage == model.RoundStage.proposal_request:
            return self._handle_proposal_request(mission, **kwargs)
        elif mission.stage == model.RoundStage.troop_proposal:
            return self._handle_troop_proposal(mission, **kwargs)
        elif mission.stage == model.RoundStage.troop_voting:
            return self._handle_troop_voting(mission, **kwargs)
        elif mission.stage == model.RoundStage.troop_voting_results:
            return self._handle_troop_voting_results(mission, **kwargs)
        elif mission.stage == model.RoundStage.mission_voting:
            return self._handle_mission_voting(mission, **kwargs)
        elif mission.stage == model.RoundStage.mission_voting_result:
            return self._handle_mission_voting_result(mission, **kwargs)
        elif mission.stage == model.RoundStage.mission_results:
            return actions.MissionUpdated(mission.game_id, mission.to_dict())

    def _handle_proposal_request(self, mission, **kwargs):
        mission.game.next_leader()
        mission.next()
        return actions.MissionUpdated(mission.game, mission.to_dict())

    def _handle_troop_proposal(self, mission, **kwargs):
        target_players = self.rules['team'][len(mission.game.players)]['mission_team'][len(mission.game.missions) - 1]
        if 'players_ids' not in kwargs:
            raise errors.InvalidPlayersNumber(0, target_players)
        elif kwargs['sid'] != mission.game.current_leader().sid:
            raise errors.NotLeader()
        members_ids = kwargs['players_ids']
        if len(members_ids) != target_players:
            raise errors.InvalidPlayersNumber(len(members_ids), target_players)

        players_ids = [p.id for p in mission.game.players]
        _ = self._create_proposal(mission.id, mission.game.current_leader().id, members_ids, players_ids)
        mission.next()
        db.session.commit()
        return actions.MissionUpdated(mission.game_id, mission.to_dict())

    def _handle_troop_voting(self, mission, **kwargs):

        player_id = db.session.query(model.Player.id) \
            .filter(db.and_(model.Player.sid == kwargs['sid'],
                            model.Player.game_id == mission.game_id,
                            model.Player.id.in_([v.voter_id for v
                                                 in mission.current_voting().votes if v.result is None]))).first()

        if 'result' not in kwargs:
            return actions.MissionUpdated(mission.game_id, mission.to_dict())
        elif player_id is None:
            raise errors.CantVote()

        mission.current_voting().vote(player_id[0], kwargs['result'])
        if mission.current_voting().is_complete():
            mission.next()
            db.session.commit()
            return self.update_mission(mission, **kwargs)

    def _handle_troop_voting_results(self, mission, **kwargs):
        voting = mission.troop_proposals[-1].voting
        voting.result = sum([v.result for v in voting.votes]) > len(voting.votes) // 2
        if voting.result:
            mission.troop_members = mission.troop_proposals[-1].members
            mission.voting = model.Voting()
            mission.voting.votes = [model.Vote(voter=player) for player in mission.troop_members]
            db.session.add(mission.voting)
            mission.next()
            db.session.commit()
            return actions.MissionUpdated(mission.game_id, mission.to_dict())
        else:
            if len(mission.troop_proposals) >= self.rules['proposals_to_lose']:
                mission._stage = model.RoundStage.mission_results
                mission.resistance_won = False
                db.session.commit()
                return actions.GameUpdated(mission.game.to_dict(), mission.game.host_id)
            mission._stage = model.RoundStage.proposal_request
            db.session.commit()
            return self.update_mission(mission, **kwargs)

    def _handle_mission_voting(self, mission, **kwargs):
        voter_ids = [v.voter_id for v in mission.current_voting().votes if v.result is None]
        player_id = db.session.query(model.Player.id) \
            .filter(db.and_(model.Player.sid == kwargs['sid'],
                            model.Player.game_id == mission.game_id,
                            model.Player.id.in_(voter_ids))).first()

        if 'result' not in kwargs:
            return actions.MissionUpdated(mission.game_id, mission.to_dict())
        elif player_id is None:
            raise errors.CantVote()

        mission.current_voting().vote(player_id[0], kwargs['result'])
        if mission.current_voting().is_complete():
            mission.next()
            db.session.commit()
            return self.update_mission(mission, **kwargs)

    def _handle_mission_voting_result(self, mission, **kwargs):
        voting = mission.voting
        voting.result = np.bitwise_not([vote.result for vote in voting.votes]).sum() < mission.num_of_fails
        mission.resistance_won = voting.result
        mission.next()
        db.session.commit()
        return self.update_mission(mission, **kwargs)


shared = GameManager()
