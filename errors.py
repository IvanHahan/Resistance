class GameError(Exception):
    pass


class InvalidPlayersNumber(Exception):

    def __init__(self, value, target):
        super().__init__(f'Invalid Players number {value}. Must be {target}')


class InsufficientPlayersNumber(Exception):

    def __init__(self, value, target):
        super().__init__(f'Insufficient players number {value}. Minimum is {target}')


class GameNotStarted(Exception):
    def __init__(self):
        super().__init__(f'Game not started')
