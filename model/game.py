import app
from app import db
from .mission import *


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

    id = db.Column(db.Integer, primary_key=True)
    stage = db.Column(db.Enum(GameStage), default=GameStage.pending, nullable=False)
    resistance_won = db.Column(db.Boolean, nullable=True)
    _leader_idx = db.Column(db.Integer, nullable=False, default=-1)

    host_id = db.Column(db.Integer, db.ForeignKey('players.id', use_alter=True, name='fk_host_id'), nullable=True)

    host = db.relationship('Player', uselist=False, foreign_keys=[host_id], post_update=True)
    players = db.relationship('Player', uselist=True, back_populates='game', cascade='all, delete-orphan',
                              foreign_keys='[Player.game_id]')
    missions = db.relationship('Mission', back_populates='game',
                               cascade='all, delete-orphan',
                               order_by='Mission.id')

    @property
    def status(self):
        if self.stage == GameStage.pending:
            return GameStatus.pending
        elif self.stage == GameStage.finished:
            return GameStatus.finished
        return GameStatus.in_progress

    def _set_stage(self, status):
        self.stage = status
        db.session.commit()

    def _new_mission(self):
        mission = Mission(game=self, num_of_fails=app.rules[len(self.players)]['fails_num'][len(self.missions) - 1])
        db.session.add(mission)
        db.session.commit()
        return mission

    def _setup(self):
        spies_idx = np.random.randint(0, len(self.players), app.rules[len(self.players)]['spies'])
        for i in range(len(self.players)):
            if i in spies_idx:
                self.players[i].role = Role.spy
            else:
                self.players[i].role = Role.resistance
        db.session.commit()

    def _complete_game(self):
        fail_missions = len([mission for mission in self.missions if mission.voting.result is False])
        success_missions = len([mission for mission in self.missions if mission.voting.result is True])
        missions_to_win = app.rules[len(self.players)]['missions_to_win']
        if fail_missions == missions_to_win:
            self.resistance_won = False
            return True
        elif success_missions == missions_to_win:
            self.resistance_won = True
            return True
        return False

    def current_mission(self):
        return self.missions[-1] if len(self.missions) > 0 else None

    def current_voting(self):
        return self.missions[-1].current_voting()

    def next_leader(self):
        if self._leader_idx == len(self.players) - 1:
            self._leader_idx = 0
        else:
            self._leader_idx += 1
        leader = self.players[self._leader_idx]
        return leader

    def add_player(self, player_id, is_host=False):
        if self.stage != GameStage.pending:
            player = None
            for p in self.players:
                if p.id == player_id:
                    player = p
            if player is not None:
                raise errors.UknownPlayer()
            return player
        elif (self.players is None or len(self.players) < 10) and self.stage == GameStage.pending:
            player = Player(name=player_id, game=self)
            if is_host:
                self.host = player
            db.session.add(player)
            db.session.commit()
            return player
        else:
            raise errors.GameFull()

    def remove_player(self, player_id):
        if self.stage == GameStage.pending:
            username = db.session.query(Player.name).filter(Player.id == player_id).first()
            db.session.query(Player).filter(Player.id == player_id).delete()
            db.session.commit()
            return username

    def current_leader(self):
        return self.players[self._leader_idx]

    def update(self, mission_state=None, **kwargs):
        return self.update_for_state(self.stage, mission_state, **kwargs)

    def update_for_state(self, state, mission_state=None, **kwargs):

        if len(self.players) not in app.rules.keys():
            raise errors.InsufficientPlayersNumber(len(self.players), min(app.rules.keys()))

        self._set_stage(state)
        if self.stage == GameStage.pending:
            return self.update_for_state(GameStage.starting)

        elif self.stage == GameStage.starting:
            self._setup()
            return self.update_for_state(GameStage.start_mission)

        elif self.stage == GameStage.start_mission:
            _ = self._new_mission()
            return self.update_for_state(GameStage.executing_mission)

        elif self.stage == GameStage.executing_mission:
            if mission_state:
                action = self.current_mission().update_for_state(mission_state, **kwargs)
            else:
                action = self.current_mission().update()
            if isinstance(action, actions.MissionComplete):
                if self._complete_game():
                    self.update_for_state(GameStage.finished)
                    return [action, actions.GameComplete(self.id, self.resistance_won, self.status)]
                else:
                    return [action, self.update_for_state(GameStage.start_mission)]
            return [action] if action is not None else []

    def to_dict(self, include_details=True):
        obj = {
            'id': self.id,
            'status': self.stage,
            'resistance_won': self.resistance_won,
            'leader_index': self._leader_idx,
            'host_id': self.host_id
        }
        if include_details:
            obj['players'] = [player.to_dict() for player in self.players]
            obj['missions'] = [mission.to_dict() for mission in self.missions]
        return obj
