from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import yaml
from flasgger import Swagger

db = SQLAlchemy()
socketio = SocketIO()
swagger = Swagger()
rules = None


def create_app(config='config.Debug'):

    global rules

    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    socketio.init_app(app)
    swagger.init_app(app)

    with app.app_context():

        db.drop_all()
        db.create_all()

    with open(app.config['RULES_PATH'], 'r') as stream:
        rules = yaml.safe_load(stream)

    import model
    import events

    return app


if __name__ == '__main__':

    app = create_app()
    socketio.run(app, host='localhost', port=5000)
