import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, send, join_room, leave_room


app = Flask(__name__)
app.config.from_object('config.Debug')

db = SQLAlchemy(app)
db.create_all()

socketio = SocketIO(app)

import events
if __name__ == '__main__':

    socketio.run(app)