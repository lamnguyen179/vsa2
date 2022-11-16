from flask import jsonify, request, g
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

from app.api import blueprint
from app.base.models import User


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.password == password:
            return False
    g.user = user
    return True


@blueprint.route('/api/token/')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})
