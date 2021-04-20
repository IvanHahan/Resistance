from os import environ as env

from utils import abs_path

POSTGRES_USER = env.get('POSTGRES_USER', 'resistance')
POSTGRES_PASSWORD = env.get('POSTGRES_PASSWORD', 'kjuyguyf24234cvbinm523b5yt6')


class Default(object):
    DEBUG = False
    VERBOSE = True
    SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5405/resistance'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RULES_PATH = abs_path('rules/basic.yml')


class Debug(Default):
    DEBUG = True
    RULES_PATH = abs_path('rules/stage.yml')


class Test(Default):
    BCRYPT_LOG_ROUNDS = 4
    TESTING = True
    WTF_CSRF_ENABLED = False
    RULES_PATH = abs_path('rules/test.yml')


class TestProd(Test):
    RULES_PATH = abs_path('rules/basic.yml')


class Heroku(Default):
    SQLALCHEMY_DATABASE_URI = env.get('DATABASE_URL', None)


class HerokuDev(Heroku):
    RULES_PATH = abs_path('rules/stage.yml')
