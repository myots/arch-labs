from collections import OrderedDict
import os
import json
from http import HTTPStatus

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import sessionmaker
app = Flask(__name__)

config = {
    'DATABASE_URI': os.environ.get('DATABASE_URI', ''),
    'HOSTNAME': os.environ['HOSTNAME'],
    'GREETING': os.environ.get('GREETING', 'Hello'),
}


app.config['SQLALCHEMY_DATABASE_URI'] = config['DATABASE_URI']
database = SQLAlchemy(app)


class User(database.Model):
    __tablename__ = "users"

    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String())
    firstname = database.Column(database.String())
    lastname = database.Column(database.String())
    email = database.Column(database.String())
    phone = database.Column(database.String())

    @property
    def jsonify(self):
        return self.__json__()

    def __json__(self):
        return OrderedDict(
            id=self.id,
            username=self.username,
            firstname=self.firstname,
            lastname=self.lastname,
            email=self.email,
            phone=self.phone,
        )

    def __repr__(self):
        return f"{self.id}: {self.username}"


def create_session():
    engine = create_engine(config['DATABASE_URI'], echo=True)
    Session = sessionmaker(engine)
    return Session()


@app.route("/")
def hello():
    return config['GREETING'] + ' from ' + config['HOSTNAME'] + '!'


@app.route("/config")
def configuration():
    return json.dumps(config)


@app.route("/user", methods=['POST'])
def create():
    username = request.form.get('username')
    if not username:
        return (
            {'code': HTTPStatus.UNPROCESSABLE_ENTITY, 'message': 'Username required'},
            HTTPStatus.UNPROCESSABLE_ENTITY
        )
    user = User(username=username)
    try:
        database.session.add(user)
        database.session.commit()
    except OperationalError as e:
        return {'code': 422, 'message': str(e)}, 422
    return '', HTTPStatus.CREATED


@app.route("/user/<int:user_id_start>/<int:user_id_end>", methods=['GET', 'DELETE'])
def user_bulk_methods(user_id_start: int, user_id_end: int):
    with create_session() as session:
        query = (
            session.query(User)
            .filter(User.id >= user_id_start, User.id <= user_id_end)
        )
        users: User = query.all()

        if request.method == 'GET':
            result, status = (
                ([user.jsonify for user in users], 200)
                if users else
                ({'code': 404, 'message': 'Users not found'}, 404)
            )
        elif request.method == 'DELETE':
            result, status = '', 204
            try:
                if users:
                    query.delete()
                    session.commit()
                else:
                    result, status = {'code': 422, 'message': 'User not found'}, 422
            except Exception as e:
                result, status = {'code': 422, 'message': str(e)}, 422

    return result, status


@app.route("/user/<int:user_id>", methods=['GET', 'DELETE', 'PUT'])
def user_methods(user_id: int):
    user: User = User.query.filter_by(id=user_id).first()
    if request.method == 'GET':
        result, status = (
            (user.jsonify, 200)
            if user else
            ({'code': 404, 'message': 'User not found'}, 404)
        )
    elif request.method == 'DELETE':
        result, status = '', 204
        try:
            if user:
                database.session.delete(user)
                database.session.commit()
            else:
                result, status = {'code': 422, 'message': 'User not found'}, 422
        except Exception as e:
            result, status = {'code': 422, 'message': str(e)}, 422
    elif request.method == 'PUT':
        user: User = User.query.filter_by(id=user_id).first()
        if not user:
            return {'code': 422, 'message': 'User not found'}, 422
        user.username = request.json.get('username') or user.username,
        user.firstname = request.json.get('firstname') or user.firstname,
        user.lastname = request.json.get('lastname') or user.lastname,
        user.email = request.json.get('email') or user.email,
        user.phone = request.json.get('phone') or user.phone,
        try:
            database.session.commit()
        except Exception as e:
            result, status = {'code': 422, 'message': str(e)}, 422
        result, status = {'code': 200, 'message': 'Used updated'}, 200

    return result, status


@app.route('/db')
def db():
    rows = []
    try:
        with create_session() as session:
            try:
                query = select(User)
                result = session.scalars(query).all()
            except ProgrammingError as e:
                rows = {'code': 503, 'message': str(e)}
            else:
                rows = [user.jsonify for user in result]
    except OperationalError as e:
        rows = {'code': 503, 'message': str(e)}
    return json.dumps(rows)


@app.route("/health")
def health():
    engine = create_engine(config['DATABASE_URI'], echo=True)
    status = HTTPStatus.OK
    try:
        with engine.connect() as connection:
            try:
                connection.execute(text("select id from users limit 1;"))
            except ProgrammingError:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
    except OperationalError:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
    return '', status


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='80', debug=True)
