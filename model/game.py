import errors
import socket_actions as actions
from .mission import *


class GameStatus(enum.Enum):
    pending = 0
    starting = 1
    start_mission = 2
    executing_mission = 3
    finished = 4


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(GameStatus), default=GameStatus.pending, nullable=False)
    paused = db.Column(db.Boolean, default=False, nullable=False)
    resistance_won = db.Column(db.Boolean, nullable=True)
    _leader_idx = db.Column(db.Integer, nullable=False, default=-1)

    host_id = db.Column(db.Integer, db.ForeignKey('players.id', use_alter=True, name='fk_host_id'), nullable=True)

    host = db.relationship('Player', uselist=False, foreign_keys=[host_id], post_update=True)
    players = db.relationship('Player', uselist=True, back_populates='game', cascade='all, delete-orphan',
                              foreign_keys='[Player.game_id]')
    missions = db.relationship('Mission', back_populates='game',
                               cascade='all, delete-orphan',
                               order_by='Mission.id')

    def _set_status(self, status):
        self.status = status
        db.session.commit()

    def _new_mission(self):
        mission = Mission(game=self, num_of_fails=app.rules[len(self.players)]['fails_num'][len(self.missions) - 1])
        db.session.add(mission)
        db.session.commit()
        return mission

    def _setup(self):
        spies_idx = np.random.randint(0, len(self.players), app.rules[len(self.players)]['spies'])
        for i in range(self.players):
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

    def current_leader(self):
        return self.players[self._leader_idx]

    def update(self):

        if self.status == GameStatus.pending:
            return

        elif self.status == GameStatus.starting:
            self._setup()
            self.next()

        elif self.status == GameStatus.start_mission:
            _ = self._new_mission()
            self.next()

        elif self.status == GameStatus.executing_mission:

            action = self.current_mission().update()
            if action == actions.mission_complete:
                if self._complete_game():
                    self.next()
                    yield [action, actions.game_complete(self.id, self.resistance_won)]
                else:
                    self._set_status(GameStatus.start_mission)
                    return [action, self.update()]
            return [action]

    def next(self):
        if len(self.players) not in app.rules.keys():
            raise errors.InsufficientPlayersNumber(len(self.players), min(app.rules.keys()))
        if self.paused:
            return actions.game_paused(self.id)
        self._set_status(GameStatus(self.status.value + 1))
        self.update()

    def to_dict(self, include_details=True):
        obj = {
            'id': self.id,
            'status': self.status,
            'resistance_won': self.resistance_won,
            'leader_index': self._leader_idx,
            'host_id': self.host_id
        }
        if include_details:
            obj['players'] = [player.to_dict() for player in self.players]
            obj['missions'] = [mission.to_dict() for mission in self.missions]
        return obj

    def pause(self):
        self.paused = True
        db.session.commit()
        return actions.game_paused(self.id)

    def resume(self):
        if self.status == GameStatus.pending:
            raise errors.GameNotStarted()

        self.paused = False
        db.session.commit()
        self.update()
