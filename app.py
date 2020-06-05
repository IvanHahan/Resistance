import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime

app = Flask(__name__)
db = SQLAlchemy(app)

app.config.from_object('config.Default')
