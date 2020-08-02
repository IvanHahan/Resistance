from utils import abs_path


class Default(object):
    DEBUG = False
    VERBOSE = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/resistance'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RULES_PATH = abs_path('rules/basic.yml')


class Debug(Default):
    DEBUG = True


class Test(Default):
    BCRYPT_LOG_ROUNDS = 4
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/resistance_test'
    # SQLALCHEMY_ECHO = True
    RULES_PATH = abs_path('rules/test_1.yml')
