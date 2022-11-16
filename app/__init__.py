# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import logging
from importlib import import_module

from flask import Flask, g
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_security import SQLAlchemyUserDatastore, current_user

from app import const

db = SQLAlchemy()
ma = Marshmallow()
login_manager = LoginManager()

logger = logging
logger.basicConfig(filename=const.LOG_PATH, level=logging.INFO,
                   format='%(asctime)s %(levelname)s %(threadName)s : '
                          '%(message)s')

logger.info("\nStarting app...")

from app.base.models import User, Role, Aggregate, Server, Storage  # noqa
user_datastore = SQLAlchemyUserDatastore(db, User, Role)


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ('base', 'home'):
        module = import_module('app.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

    for home_module in ('account', 'volume', 'aggregate'):
        module = import_module('app.home.{}'.format(home_module))
    app.register_blueprint(module.blueprint)

    # API
    api = import_module('app.api.main'.format(module_name))
    app.register_blueprint(api.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        # for master data in DB
        db.create_all()

        # Create roles and user for admin
        if not user_datastore.find_role(const.R_ADMIN):
            user_datastore.create_role(name=const.R_ADMIN)

        if not user_datastore.find_user(username='admin'):
            user_datastore.create_user(email='admin',
                                       username='admin',
                                       password=const.OPENSTACK_ADMIN_PASSWORD)

        # Create roles and user for normal user
        if not user_datastore.find_role(const.R_USER_PHYSICAL):
            user_datastore.create_role(name=const.R_USER_PHYSICAL)
        if not user_datastore.find_role(const.R_USER_CLOUD):
            user_datastore.create_role(name=const.R_USER_CLOUD)

        if not user_datastore.find_user(username="physical"):
            user_datastore.create_user(email='physical',
                                       username="physical",
                                       password=const.
                                       OPENSTACK_PHYSICAL_PASSWORD)
        if not user_datastore.find_user(username="cloud"):
            user_datastore.create_user(email='cloud',
                                       username="cloud",
                                       password=const.OPENSTACK_CLOUD_PASSWORD)
        db.session.commit()

        user_datastore.add_role_to_user('admin', const.R_ADMIN)
        user_datastore.add_role_to_user('physical',
                                        const.R_USER_PHYSICAL)
        user_datastore.add_role_to_user('cloud',
                                        const.R_USER_CLOUD)
        db.session.commit()

    @app.before_request
    def inject_global_proxy():
        g.c = const
        g.user = current_user

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def register_ma(app):
    ma.init_app(app)


def create_app(config):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    register_ma(app)
    return app
