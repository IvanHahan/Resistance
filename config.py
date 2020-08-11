from utils import abs_path


class Default(object):
    DEBUG = False
    VERBOSE = True
    SQLALCHEMY_DATABASE_URI = 'postgres://resistance:kjuyguyf24234cvbinm523b5yt6@db:5405/resistance'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RULES_PATH = abs_path('rules/basic.yml')


class Debug(Default):
    DEBUG = True
    RULES_PATH = abs_path('rules/test.yml')
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/resistance_test'
    # SQLALCHEMY_ECHO = True


class Test(Default):
    BCRYPT_LOG_ROUNDS = 4
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'postgres://resistance:kjuyguyf24234cvbinm523b5yt6@db:5405/resistance_test'
    RULES_PATH = abs_path('rules/test.yml')


class TestProd(Default):
    RULES_PATH = abs_path('rules/basic.yml')
