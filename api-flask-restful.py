#!/usr/bin/env python
import os
from flask_restful import Resource, Api
from flask import Flask, abort, request, jsonify, g, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
api = Api(app)

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


class new_user(Resource):
    def post(self):
        username = request.json.get('username')
        password = request.json.get('password')
        if username is None or password is None:
            abort(400) #missing arguments
        if User.query.filter_by(username=username).first() is not None:
            abort(400) # existing user
        user = User(username=username)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
        return {'username': user.username}
            


class get_user(Resource):
    def get(self, id):
        user = User.query.get(id)
        if not user:
            abort(400)
        return {'username': user.username}


class get_auth_token(Resource):
    @auth.login_required
    def get(self):
        token = g.user.generate_auth_token(600)
        return {'token': token.decode('ascii'), 'duration': 600}


class get_resource(Resource):
    @auth.login_required
    def get(self):
        return {'data': 'Hello, %s!' % g.user.username}

api.add_resource(new_user, '/api/users')
api.add_resource(get_user, '/api/users/<int:id>')
api.add_resource(get_auth_token, '/api/token')
api.add_resource(get_resource, '/api/resource')

if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(debug=True)
