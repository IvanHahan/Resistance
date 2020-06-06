import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime

app = Flask(__name__)
app.config.from_object('config.Default')

db = SQLAlchemy(app)
db.create_all()
