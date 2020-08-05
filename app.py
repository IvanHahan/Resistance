from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import yaml
from flasgger import Swagger

db = SQLAlchemy()
socketio = SocketIO()
swagger = Swagger()
from game_manager import GameManager

game_manager = GameManager()

def create_app(config='config.Debug'):

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config.from_object(config)

    db.init_app(app)
    socketio.init_app(app)
    swagger.init_app(app)

    with app.app_context():

        db.drop_all()
        db.create_all()

    with open(app.config['RULES_PATH'], 'r') as stream:
        rules = yaml.safe_load(stream)
        game_manager.configure(rules)

    return app


# from flask_socketio import send, emit
# @socketio.on('connect', namespace='test')
# def connect():
#     print('connected')
#     send('connected')
#     emit('pizda')
#
# @socketio.on('pidor', namespace='test')
# def pidor(hui):
#     print('pidor', hui)
#     send('Ti pidor')

# @socketio.on('message', namespace='test')
# def message(mes):
#     print(mes)
#     send('recieved')

from events import *
from model import *


if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='192.168.0.102', port=5000)
