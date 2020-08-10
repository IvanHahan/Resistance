from utils import abs_path


class Default(object):
    DEBUG = False
    VERBOSE = True
    SQLALCHEMY_DATABASE_URI = 'postgres://resistance:fo23h5iu32h5i324uhiuh5324@db:5405/resistance'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RULES_PATH = abs_path('rules/basic.yml')


class Debug(Default):
    DEBUG = True
    RULES_PATH = abs_path('rules/test.yml')


class Test(Default):
    BCRYPT_LOG_ROUNDS = 4
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'postgres://resistance:fo23h5iu32h5i324uhiuh5324@db:5405/resistance_test'
    RULES_PATH = abs_path('rules/test.yml')


class TestProd(Default):
    RULES_PATH = abs_path('rules/basic.yml')
