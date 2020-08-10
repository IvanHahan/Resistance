from logging import getLogger

import yaml
from flask import Flask

from logger import set_global_config
from services import db, socketio, swagger
from events import *


def create_app(config='config.Debug'):
    global game_manager, event_logger

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config.from_object(config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    swagger.init_app(app)

    set_global_config()
    event_logger = getLogger('Events')

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
