from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from database import get_db_connection

auth_blueprint = Blueprint('auth', __name__)

# Login route to authenticate users
@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Connect to the database
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user and check_password_hash(user['password'], password):
        # Create a JWT token
        access_token = create_access_token(identity={'user_id': user['user_id'], 'role': user['role']})
        return jsonify({"access_token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Protected route
@auth_blueprint.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({
        "message": f"Hello, {current_user['role']}!", 
        "user_id": current_user['user_id']
    }), 200
