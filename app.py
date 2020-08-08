from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import yaml
from flasgger import Swagger
from logger import get_logger

db = SQLAlchemy()
socketio = SocketIO()
swagger = Swagger()
app_logger = get_logger('events')

from events import *
from model import *


def create_app(config='config.Debug'):

    global game_manager

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


if __name__ == '__main__':

    app = create_app()

    socketio.run(app, host='192.168.0.102', port=5000)
