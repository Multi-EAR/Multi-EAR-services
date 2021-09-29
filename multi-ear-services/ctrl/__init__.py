class BaseCfg(object):
    SECRET_KEY = 'SuperS3cretKEY_1222'
    DEBUG = False
    TESTING = False

class DevelopmentCfg(BaseCfg):
    DEBUG = True
    TESTING = True

class TestingCfg(BaseCfg):
    DEBUG = False
    TESTING = True

class ProductionCfg(BaseCfg):
    SECRET_KEY = 'HvFDDcfsnd__9nbCdgsada' 
    DEBUG = False
    TESTING = False
