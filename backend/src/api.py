import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()


# ROUTES


@app.route('/drinks')
def get_drinks():
    try:
        drinks = [d.short() for d in Drink.query.all()]

        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except Exception:
        abort(500)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_detailed_drinks(payload):
    try:
        drinks = [d.long() for d in Drink.query.all()]
        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except Exception:
        abort(500)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    data = request.get_json()
    if "title" not in data:
        abort(400, "request is missing drink title")

    if "recipe" not in data:
        abort(400, "request is missing recipe")

    try:

        title = data.get('title')
        recipe = json.dumps(data.get('recipe'))

        new_drink = Drink(title=title, recipe=recipe)
        Drink.insert(new_drink)

        drink = new_drink.long()

        return jsonify({
            "sucess": True,
            "drinks": drink
        })

    except Exception:
        abort(500)


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drinks(payload, id):
    data = request.get_json()
    drink = Drink.query.filter_by(id=id).one_or_none()

    if drink is None:
        abort(404, 'cannot find drink id')

    try:

        if "title" in data:
            drink.title = data.get("title")

        if "recipe" in data:
            drink.recipe = json.dumps(data.get("recipe"))

        Drink.update(drink)

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })

    except Exception:
        abort(500)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):

    drink = Drink.query.filter_by(id=id).one_or_none()

    if drink is None:
        abort(404, 'drink id not found')

    Drink.delete(drink)

    return jsonify({
        "success": True,
        "delete": id
    })


# Error Handling

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": error.description
    }), 404


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": error.description
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": error.description
    }), 400


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": error.description
    }), 500


@app.errorhandler(AuthError)
def authentication_error(e):
    return jsonify(e.error), e.status_code
