from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash
from database import get_db_connection
import re

auth_blueprint = Blueprint('auth', __name__)

# Login route to authenticate users
@auth_blueprint.route('/login', methods=['POST'])
def login():
    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: aa123
            password:
              type: string
              example: secret123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            access_token:
              type: string
              example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
      400:
        description: Missing username or password
        schema:
          type: object
          properties:
            error:
              type: string
              example: Username and password are required
      401:
        description: Invalid credentials
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid credentials
    """

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Sanitize username to prevent SQL injection
    # Example using regex to allow only alphanumeric characters and underscores
    username = re.sub(r"[^a-zA-Z0-9_]", "", username) 

    # Connect to the database
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user and check_password_hash(user['password'], password):
        # Create a JWT token
        access_token = create_access_token(
            identity=user['user_id'], 
            additional_claims={'role': user['role']}
        )
        return jsonify({"access_token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Protected route
@auth_blueprint.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Protected Route
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: "JWT Bearer token. Example: 'Bearer <your_token>'"
    responses:
      200:
        description: Access granted to protected resource
        schema:
          type: object
          properties:
            user_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            message:
              type: string
              example: Hello, ADMIN!
      401:
        description: Missing or invalid token
        schema:
          type: object
          properties:
            error:
              type: string
              example: Missing Authorization Header
    """

    current_user = get_jwt_identity()
    claims = get_jwt()
    return jsonify({
        "user_id": current_user,
        "message": f"Hello, {claims['role']}!"
    }), 200
