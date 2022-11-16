# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from decouple import config

from app import const


class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    SECRET_KEY = 'VSA2-easy-storage'

    # This will create a file in <app> FOLDER
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        config('DB_ENGINE', default=const.DB_ENGINE),
        config('DB_USERNAME', default=const.DB_USERNAME),
        config('DB_PASS', default=const.DB_PASSWORD),
        config('DB_HOST', default=const.DB_HOST),
        config('DB_PORT', default=const.DB_PORT),
        config('DB_NAME', default=const.DB_NAME)
    )


class DebugConfig(Config):
    DEBUG = const.DEBUG
    if DEBUG:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(Config.basedir, 'vsa2_db.sqlite3')
    else:
        SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
            config('DB_ENGINE', default=const.DB_ENGINE),
            config('DB_USERNAME', default=const.DB_USERNAME),
            config('DB_PASS', default=const.DB_PASSWORD),
            config('DB_HOST', default=const.DB_HOST),
            config('DB_PORT', default=const.DB_PORT),
            config('DB_NAME', default=const.DB_NAME)
        )


# Load all possible configurations
config_dict = {
    'host': const.APP_LISTEN,
    'port': const.APP_PORT,
    'Production': ProductionConfig,
    'Debug': DebugConfig
}

