from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import yaml
from flasgger import Swagger
from logger import set_global_config
from logging import getLogger


db = SQLAlchemy()
socketio = SocketIO()
swagger = Swagger()
from game_manager import GameManager
game_manager = GameManager()
set_global_config()
event_logger = getLogger('Events')
