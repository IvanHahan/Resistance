import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, send, join_room, leave_room


app = Flask(__name__)
app.config.from_object('config.Debug')

db = SQLAlchemy(app)
db.drop_all()

socketio = SocketIO(app)

import events
import model

if __name__ == '__main__':

    db.create_all()
    socketio.run(app)