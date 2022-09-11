import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
setup_db(app)
CORS(app)


@app.after_request
def after_request(response):

    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET,POST,DELETE"
    )
    response.headers.add(
        "Access-Control-Allow-Credentials", "true"
    )
    return response


db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def get_drinks():
    '''return all drinks with short() data representation'''
    try:
        drinks = Drink.query.all()
        drinks = [drink.short() for drink in drinks]
        return jsonify({
            'success': True,
            'drinks': drinks
        }), 200
    except BaseException:
        abort(500)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def drinks_detail(payload):
    '''return all drinks with long() data representation'''
    try:
        drinks = Drink.query.all()
        drinks = [drink.long() for drink in drinks]
        return jsonify({
            'success': True,
            'drinks': drinks
        })
    except BaseException:
        abort(500)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    '''create a new drink'''
    try:
        data = request.get_json()
        title = data.get('title', None)
        recipe = data.get('recipe', None)
        # check if title and recipe are provided
        if not title or not recipe:
            abort(400)
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except IntegrityError:
        # if drink already exists
        abort(422)
    except BaseException:
        abort(400)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    '''update drink data to passed data'''
    try:
        drink = Drink.query.get(drink_id)
        if drink is None:
            abort(404)
        data = request.get_json()
        title = data.get('title')
        recipe = data.get('recipe')
        # check if title and recipe are provided
        if title is not None:
            drink.title = title
        if recipe is not None:
            drink.recipe = json.dumps(recipe)
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except IntegrityError:
        # if drink title already exists
        abort(422)
    except BaseException:
        abort(400)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    '''delete drink'''
    drink = Drink.query.get(drink_id)
    # check if drink exists
    if not drink:
        abort(404)
    drink.delete()
    return jsonify({
        'success': True,
        'delete': drink_id
    }), 200

# Error Handling
# Example error handling for unprocessable entity


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
        }), 400


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Server Error"
        }), 500


@app.errorhandler(405)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "Method not allowed"
        }), 405


@app.errorhandler(404)
def not_found(error):
    return (jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404, )


@app.errorhandler(AuthError)
def auth_error(error):
    print(error)
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code


if __name__ == "__main__":
    app.debug = True
    app.run()
