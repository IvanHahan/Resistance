from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import yaml
from flasgger import Swagger
import logging

db = SQLAlchemy()
socketio = SocketIO()
swagger = Swagger()

from events import *
from game_manager import GameManager
game_manager = GameManager()
handlers = [logging.StreamHandler()]
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=handlers)


def create_app(config='config.Debug'):
    global game_manager

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config.from_object(config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
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
