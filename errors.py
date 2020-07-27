class GameError(Exception):
    pass


class InvalidPlayersNumber(GameError):

    def __init__(self, value, target):
        super().__init__(f'Invalid Players number {value}. Must be {target}')


class VoteNotFound(GameError):

    def __init__(self):
        super().__init__(f'Vote or player not found')


class InsufficientPlayersNumber(GameError):

    def __init__(self, value, target):
        super().__init__(f'Insufficient players number {value}. Minimum is {target}')


class GameNotStarted(GameError):
    def __init__(self):
        super().__init__(f'Game not started')


class GameFull(GameError):
    def __init__(self):
        super().__init__(f'The game is full')


class UknownPlayer(GameError):
    def __init__(self):
        super().__init__(f'Unknown Player')
