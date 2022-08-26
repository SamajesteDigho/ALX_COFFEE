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

'''
@TODO uncomment the following line to initialize the database
!!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!!! Running this function will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    drinks = [x.short() for x in drinks]
    return jsonify({
        'drinks': drinks,
        'success': True
    }, 200), 200


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(permission):
    try:
        drinks = Drink.query.all()
        drinks = [x.long() for x in drinks]
        return jsonify({
            'drinks': drinks,
            'success': True
        }, 200), 200
    except:
        abort(500)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly 
        created drink or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drinks')
def create_drink(permission):
    data = json.loads(request.data)
    # Verify if the title was provided
    if 'title' in data.keys():
        title = data['title']
    else:
        raise AuthError({
            'code': 'MALFORMED_JSON',
            'description': 'You must provide the title for the drink.'
        }, 401)
    # Collect the recipe if it's present
    if 'recipe' in data.keys():
        recipe = '[{' + \
                 '"name":"' + str(data['recipe']['name']) + \
                 '", "color":"' + str(data['recipe']['color']) + \
                 '", "parts":"' + str(data['recipe']['parts']) + \
                 '"}]'
    else:
        recipe = None

    try:
        drink = Drink(title=title, recipe=recipe)
        drink.insert()
        #drink = Drink.query.filter_by(title=title).first()
        return jsonify({
            'drinks': [drink.long()],
            'success': True
        }, 200)
    except Exception as e:
        # If the provided title already exist
        return jsonify({
            'success': False,
            'message': e.__str__()
        })
    except:
        abort(422)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the
        updated drink or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drink(permission, id):
    drink = Drink.query.get(id)
    if drink is None:
        abort(500)
    data = json.loads(request.data)
    if 'title' in data.keys():
        drink.title = data['title']
    if 'recipe' in data.keys():
        recipe = '[{' + \
                 '"name":"' + str(data['recipe']['name']) + \
                 '", "color":"' + str(data['recipe']['color']) + \
                 '", "parts":"' + str(data['recipe']['parts']) + \
                 '"}]'
        drink.recipe = recipe
    try:
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'reason': e.__str__()
        })


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(permission, id):
    drink = Drink.query.get(id)
    if drink is None:
        abort(404)
    try:
        drink.delete()
        return jsonify({
            'success': True,
            'delete': id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'reason': e.__str__()
        })


# Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def notfound(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def authError(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code

