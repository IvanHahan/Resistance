class GameError(Exception):
    pass


class InvalidPlayersNumber(Exception):

    def __init__(self, value, target):
        super().__init__(f'Invalid Players number {value}. Must be {target}')
