from os import environ as env

from utils import abs_path

POSTGRES_USER = env.get('POSTGRES_USER', None)
POSTGRES_PASSWORD = env.get('POSTGRES_PASSWORD', None)

class Default(object):
    DEBUG = False
    VERBOSE = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/resistance_test'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RULES_PATH = abs_path('rules/basic.yml')


class Docker(Default):
    SQLALCHEMY_DATABASE_URI = f'postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5405/resistance'


class Heroku(Default):
    SQLALCHEMY_DATABASE_URI = env['DATABASE_URL']


class HerokuDev(Heroku):
    RULES_PATH = abs_path('rules/test.yml')


class LocalDebug(Default):
    DEBUG = True
    RULES_PATH = abs_path('rules/test.yml')
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/resistance_test'


class DockerTest(Docker):
    BCRYPT_LOG_ROUNDS = 4
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = f'postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5405/resistance_test'
    RULES_PATH = abs_path('rules/test.yml')
