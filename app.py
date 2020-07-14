import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, send, join_room, leave_room

db = SQLAlchemy()
socketio = SocketIO()


def create_app(config='config.Debug'):

    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    socketio.init_app(app)

    with app.app_context():

        db.drop_all()
        db.create_all()

    import events
    import model

    return app


if __name__ == '__main__':

    app = create_app()
    socketio.run(app, host='localhost', port=5000)
