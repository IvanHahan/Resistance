import model
from app import db
import numpy as np
from flask_socketio import emit, join_room, leave_room


def create_game(username):
    game = model.Game()
    player = model.Player(name=username, game=game)
    game.host = player

    db.session.add(game)
    db.session.add(player)
    db.session.commit()
    join_room(game.id)
    # emit('game_created')


def join_game(game_id, username):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    if len(game.players) < 10:
        player = model.Player(name=username)
        player.game = game
        db.session.add(player)
        db.session.commit()


def update_voting(voting_id, player_id, result):
    voting = db.session.query(model.Voting).filter(model.Voting.id == voting_id).first()
    vote = db.session.query(model.Vote).filter(db.and_(model.Voting.id == voting_id,
                                                       model.Vote.voter_id == player_id)).first()
    vote.result = result
    vote_complete = np.bitwise_or.reduce([vote.result is None for vote in voting.votes]) == False
    if vote_complete:
        update_mission(voting.mission.id)
    else:
        return


def update_game(game_id):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()

    if game.status == model.GameStatus.pending:
        return

    elif game.status == model.GameStatus.start_mission:
        mission = model.Mission(game=game)
        db.session.add(mission)
        db.session.commit()
        update_mission(mission.id)
        return

    elif game.status == model.GameStatus.end_mission:
        fail_missions = len([mission for mission in game.missions if mission.voting.result is False])
        success_missions = len([mission for mission in game.missions if mission.voting.result is True])
        if fail_missions == 3:
            game.resistance_won = False
        elif success_missions == 3:
            game.resistance_won = True
        return

    elif game.status == model.GameStatus.finished:
        """game finished"""
        return


def update_mission(mission_id, *args, **kwargs):
    mission = db.session.query(model.Mission).filter(model.Mission.id == mission_id).first()

    if mission.stage == model.RoundStage.proposal_request:
        if mission.game.leader_idx == len(mission.game.players) - 1:
            mission.game.leader_idx = 0
        else:
            mission.game.leader_idx += 1
        leader = mission.game.players[mission.game.leader_idx]
        emit('query_proposal', leader.id)

    elif mission.stage == model.RoundStage.troop_proposal:
        players_ids = args[0]
        players = db.session.query(model.Player).filter(model.Player.id.in_(players_ids)).first()
        proposal = model.TroopProposal(players=players,
                                       proposer=mission.game.players[mission.game.leader_idx],
                                       mission=mission)
        voting = model.Voting(mission=mission)
        voting.votes = [model.Vote(voter=player) for player in players]
        proposal.voting = voting
        db.session.add(proposal)
        db.session.add(voting)
        db.session.commit()
        emit('start_voting', [player.id for player in mission.game.players])

    elif mission.stage == model.RoundStage.troop_voting:
        voting = mission.troop_proposals[-1].voting
        voting.result = sum([v.result for v in voting.voting.votes]) > len(voting.voting.votes) // 2
        if voting.result:
            mission.troop_members = mission.troop_proposals[-1].members
            db.session.commit()
            emit('start_voting', [player.id for player in mission.troop_members.members])
        else:
            mission.stage = model.RoundStage.proposal_request

            update_mission(mission_id)

    elif mission.stage == model.RoundStage.mission_voting:
        voting = mission.voting
        voting.result = np.bitwise_or.reduce([vote.result for vote in voting.votes])
        mission.stage = model.RoundStage.mission_results
        emit('mission_complete')

    elif mission.stage == model.RoundStage.mission_results:
        """mission complete"""

    return


def start_game(game_id):
    game = db.session.query(model.Game).filter(model.Game.id == game_id).first()
    game.status = model.GameStatus.start_mission
    db.session.commit()
    update_game(game_id)


def make_proposal(mission_id, player_ids):
    mission = db.session.query(model.Mission).filter(model.Mission.id == mission_id).first()
    mission.stage = model.RoundStage.troop_proposal
    db.session.commit()
    update_mission(mission_id, player_ids)