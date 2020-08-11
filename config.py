from utils import abs_path
from os import environ as env

POSTGRES_USER = env['POSTGRES_USER']
POSTGRES_PASSWORD = env['POSTGRES_PASSWORD']

class Default(object):
    DEBUG = False
    VERBOSE = True
    SQLALCHEMY_DATABASE_URI = f'postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5405/resistance'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RULES_PATH = abs_path('rules/basic.yml')


class Debug(Default):
    DEBUG = True
    RULES_PATH = abs_path('rules/test.yml')
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/resistance_test'


class Test(Default):
    BCRYPT_LOG_ROUNDS = 4
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = f'postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5405/resistance_test'
    RULES_PATH = abs_path('rules/test.yml')


class TestProd(Default):
    RULES_PATH = abs_path('rules/basic.yml')
