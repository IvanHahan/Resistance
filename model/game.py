from .mission import *
import errors
from app import db
from .model import *


class GameStage(enum.Enum):
    pending = 0
    starting = 1
    start_mission = 2
    executing_mission = 3
    finished = 4


class GameStatus(enum.Enum):
    pending = 0
    in_progress = 1
    finished = 2


class Game(db.Model):
    __tablename__ = 'games'

    missions_to_win = 2

    id = db.Column(db.Integer, primary_key=True)
    stage = db.Column(db.Enum(GameStage), default=GameStage.pending, nullable=False)
    resistance_won = db.Column(db.Boolean, nullable=True)
    _leader_idx = db.Column(db.Integer, nullable=False, default=-1)

    host_id = db.Column(db.Integer, db.ForeignKey('players.id', use_alter=True, name='fk_host_id', ondelete='cascade'), nullable=True)

    host = db.relationship('Player', uselist=False, foreign_keys=[host_id], post_update=True)
    players = db.relationship('Player', uselist=True, back_populates='games', cascade='all, delete',
                              secondary=player_game_association, order_by='Player.id')
    missions = db.relationship('Mission', back_populates='game',
                               cascade='all, delete-orphan',
                               order_by='Mission.id')

    # @property
    # def players(self):

    @property
    def status(self):
        if self.stage == GameStage.pending:
            return GameStatus.pending
        elif self.stage == GameStage.finished:
            return GameStatus.finished
        return GameStatus.in_progress

    def next(self):
        self.stage = GameStage(int(self.stage.value) + 1)
        return self.stage

    def setup(self, spies_num):
        spies_idx = np.random.randint(0, len(self.players), spies_num)
        for i in range(len(self.players)):
            if i in spies_idx:
                self.players[i].role = Role.spy
            else:
                self.players[i].role = Role.resistance

        self._leader_idx = np.random.randint(0, len(self.players))

    def _complete_game(self):

        fail_missions = len([mission for mission in self.missions if mission.resistance_won is False])
        success_missions = len([mission for mission in self.missions if mission.resistance_won is True])
        if fail_missions == self.missions_to_win:
            self.resistance_won = False
            return True
        elif success_missions == self.missions_to_win:
            self.resistance_won = True
            return True
        return False

    def current_mission(self):
        return self.missions[-1] if len(self.missions) > 0 else None

    def current_voting(self):
        return self.missions[-1].current_voting()

    def next_leader(self):
        if self._leader_idx >= len(self.players) - 1:
            self._leader_idx = 0
        else:
            self._leader_idx += 1
        leader = self.players[self._leader_idx]
        return leader

    def current_leader(self):
        try:
            return self.players[self._leader_idx]
        except IndexError:
            return None

    def update(self, mission_state=None, **kwargs):
        return self.update_for_state(self.stage, mission_state, **kwargs)

    def update_for_state(self, state, mission_state=None, **kwargs):

        self._set_stage(state)
        if self.stage == GameStage.pending:
            return self.update_for_state(GameStage.starting)

        elif self.stage == GameStage.starting:
            self._setup()
            return self.update_for_state(GameStage.start_mission)

        elif self.stage == GameStage.start_mission:
            _ = self._new_mission()
            return [actions.GameUpdated(self.to_dict(include_details=False)),
                    *self.update_for_state(GameStage.executing_mission)]

        elif self.stage == GameStage.executing_mission:
            if mission_state:
                action = self.current_mission().update_for_state(mission_state, **kwargs)
            else:
                action = self.current_mission().update()
            if self.current_mission().stage == RoundStage.mission_results:
                if self._complete_game():
                    self.update_for_state(GameStage.finished)
                    return [action, actions.GameUpdated(self.to_dict(include_details=False))]
                else:
                    return [action, self.update_for_state(GameStage.start_mission)]
            return [action] if action is not None else []

    def to_dict(self, include_details=True):
        obj = {
            'id': self.id,
            'stage': self.stage.name,
            'host_name': self.host.name,
        }
        if include_details:
            obj['details'] = {

                'host_id': self.host_id,
                'leader_id': self.current_leader().id if self.current_leader() is not None else None,
                'players': [player.to_dict() for player in self.players],
                'missions': [mission.to_dict() for mission in self.missions],
                'resistance_won': self.resistance_won,
            }
        return obj
