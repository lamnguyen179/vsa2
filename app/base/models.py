# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import datetime
import uuid

from flask_login import UserMixin
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from sqlalchemy import (
    Column, String, Float, Boolean,
    BigInteger, ForeignKey, DateTime, Integer
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app import db, login_manager

PLAIN_TEXT_TOKEN = "a4f57ba5-b9cf-401d-add8-900e759eb1af"


class Aggregate(db.Model):
    __tablename__ = 'Aggregate'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True)

    def __repr__(self):
        return self.name


class Server(db.Model):
    __tablename__ = 'Server'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip = Column(String(50), unique=True)
    hostname = Column(String(50))
    aggregate_id = Column(String(50), ForeignKey('Aggregate.id'))
    aggregate = relationship('Aggregate', backref='servers')

    def __repr__(self):
        return self.ip


class Storage(db.Model):
    __tablename__ = 'Storage'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True)
    aggregate_id = Column(String(50), ForeignKey('Aggregate.id'))
    aggregate = relationship('Aggregate', backref='storages')

    def __repr__(self):
        return self.name


class Role(db.Model):
    __tablename__ = 'Role'
    id = Column(db.Integer(), primary_key=True)
    name = Column(db.String(50), unique=True)


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = Column(db.Integer(), primary_key=True)
    user_id = Column(String(50), db.ForeignKey('User.id', ondelete='CASCADE'))
    role_id = Column(db.Integer(), db.ForeignKey('Role.id', ondelete='CASCADE'))


class User(db.Model, UserMixin):
    __tablename__ = 'User'

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True)
    email = Column(String(255), unique=True, nullable=True)
    password = Column(String(255))
    active = Column(Boolean, nullable=False, server_default='1')
    roles = db.relationship('Role', secondary='user_roles',
                            backref=db.backref('users', lazy='dynamic'))

    def generate_auth_token(self, expiration=600):
        s = Serializer(PLAIN_TEXT_TOKEN, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(PLAIN_TEXT_TOKEN)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user

    def has_role(self, role):
        for r in self.roles:
            if role == r.name:
                return True
        return False

    def __repr__(self):
        return str(self.username)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None
