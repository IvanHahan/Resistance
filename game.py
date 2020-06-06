import model
from app import db
import numpy as np


def create_game():
    player = model.Player(name='Ivan')
    game = model.Game(host=player)
    player.game = game

    db.session.add(player)
    db.session.add(game)
    db.session.commit()


def join_game(game_id):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    if len(game.players) < 10:
        player = model.Player(name='Mark')
        player.game = game
        db.session.add(player)
        db.session.commit()


def make_proposal(mission_id, player_ids):
    mission = db.session.query(model.Mission).filter(model.Mission.id == mission_id).first()
    players = db.session.query(model.Player).filter(model.Player.id.in_(player_ids)).first()
    proposal = model.TroopProposal(players=players, proposer=mission.game.leader)
    voting = model.Voting()
    proposal.voting = voting
    db.session.add(proposal)
    db.session.add(voting)
    db.session.commit()


def query_proposal(player):
    return [0, 1, 2]


def update_voting(voting_id):
    voting = db.session.query(model.Voting).filter(model.Voting.id == voting_id).first()
    vote_complete = np.bitwise_or.reduce([vote.result is None for vote in voting.votes]) == False
    if vote_complete:
        return
    else:
        """wait others"""
        pass


def make_vote(voting_id, player_id, result):
    vote = db.session.query(model.Vote).filter(db.and_(model.Voting.id == voting_id,
                                                         model.Vote.voter_id == player_id)).first()
    vote.result = result
    db.session.commit()
    update_voting(voting_id)


def update_game(game_id):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()

    if game.status == model.GameStatus.pending:
        pass

    elif game.status == model.GameStatus.ongoing:
        mission = model.Mission(game=game)
        db.session.commit()
        update_mission(mission.id)
        fail_missions = len([mission for mission in game.missions if mission.voting.result is False])
        success_missions = len([mission for mission in game.missions if mission.voting.result is True])
        if fail_missions == 3:
            game.resistance_won = False
            game.status = model.GameStatus.finished
        elif success_missions == 3:
            game.resistance_won = True
            game.status = model.GameStatus.finished

    elif game.status == model.GameStatus.finished:
        """game finished"""
        return

    update_game(game_id)


def update_mission(mission_id):
    mission = db.session.query(model.Mission).filter(model.Mission.id == mission_id).first()

    if mission.stage == model.RoundStage.troop_proposal:
        if mission.game.leader_idx == len(mission.game.players) - 1:
            mission.game.leader_idx = 0
        else:
            mission.game.leader_idx += 1
        player_ids = query_proposal(mission.game.players[mission.game.leader_idx])
        make_proposal(mission.id, player_ids)
        mission.stage = model.RoundStage.troop_voting

    elif mission.stage == model.RoundStage.troop_voting:
        start_voting(mission.troop_proposals[-1].voting.votes)
        voting = mission.troop_proposals[-1].voting
        voting.result = sum([v.result for v in voting.voting.votes]) > len(voting.voting.votes) // 2
        if voting.result:
            mission.stage = model.RoundStage.mission_voting
        else:
            mission.stage = model.RoundStage.troop_proposal
        db.session.commit()

    elif mission.stage == model.RoundStage.mission_voting:
        voting = mission.voting
        voting.result = np.bitwise_or.reduce([vote.result for vote in voting.votes])
        mission.stage = model.RoundStage.mission_results

    elif mission.stage == model.RoundStage.mission_results:
        """mission complete"""
        return

    update_mission(mission_id)


def start_game(game_id):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    game.status = model.GameStatus.ongoing

    db.session.commit()




