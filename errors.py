class GameError(Exception):
    """Game error"""
    pass


class InvalidPlayersNumber(GameError):

    def __init__(self, value, target):
        super().__init__(f'Invalid Players number {value}. Must be {target}')


class VoteNotFound(GameError):

    def __init__(self):
        super().__init__(f'Vote or player not found')


class InsufficientPlayersNumber(GameError):

    def __init__(self):
        super().__init__(f'Insufficient players number')


class GameNotStarted(GameError):
    def __init__(self):
        super().__init__(f'Game not started')


class NotLeader(GameError):
    def __init__(self):
        super().__init__(f'You are not current leader')


class CantVote(GameError):
    def __init__(self):
        super().__init__(f'You cannot vote')


class WrongMissionState(GameError):
    def __init__(self):
        super().__init__(f'Wrong mission state')


class GameFull(GameError):
    def __init__(self):
        super().__init__(f'The game is full')


class UknownPlayer(GameError):
    def __init__(self):
        super().__init__(f'Unknown Player')


class GameNotFound(GameError):
    def __init__(self):
        super().__init__(f'Game not found')


class GameFinished(GameError):
    def __init__(self):
        super().__init__(f'Game finished')



class ForbiddenAction(GameError):
    def __init__(self):
        super().__init__(f'You are not allowed to do that')
