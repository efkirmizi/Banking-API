from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
import uuid
from database import get_db_connection
from .admin import admin_required

user_blueprint = Blueprint('user', __name__)

# create a new user
@user_blueprint.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: john_doe
            password:
              type: string
              example: my_secure_password
            role:
              type: string
              enum: [ADMIN, USER]
              example: USER
            customer_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
    responses:
      201:
        description: User created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: User created successfully
            user_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
      400:
        description: Validation error
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'USER')
        customer_id = data.get('customer_id')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        if role not in ['ADMIN', 'USER']:
            return jsonify({"error": "Invalid role specified"}), 400

        hashed_password = generate_password_hash(password)
        user_id = str(uuid.uuid4())
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO user (user_id, username, password, role, customer_id)
            VALUES (%s, %s, %s, %s, %s)""",
            (user_id, username, hashed_password, role, customer_id)
        )
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "User created successfully", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# get all users
@user_blueprint.route('/users', methods=['GET'])
@admin_required
def get_users():
    """
    Get all users
    ---
    tags:
      - Users
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of users
        schema:
          type: array
          items:
            type: object
            properties:
              user_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174000
              username:
                type: string
                example: john_doe
              role:
                type: string
                enum: [ADMIN, USER]
                example: USER
              customer_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174000
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection().cursor()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT user_id, username, role, customer_id FROM user")
        users = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# get a specific user by ID
@user_blueprint.route('/users/<user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """
    Get a specific user by ID
    ---
    tags:
      - Users
    security:
      - BearerAuth: []  
    parameters:
      - name: user_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174000
    responses:
      200:
        description: User details
        schema:
          type: object
          properties:
            user_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            username:
              type: string
              example: john_doe
            role:
              type: string
              example: ADMIN
            customer_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
      404:
        description: User not found
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for user_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, username, role, customer_id FROM user WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# update a user
@user_blueprint.route('/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """
    Update a user's details
    ---
    tags:
      - Users
    security:
      - BearerAuth: []
    parameters:
      - name: user_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174000
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: john_doe_updated
            password:
              type: string
              example: new_secure_password
            role:
              type: string
              enum: [ADMIN, USER]
              example: USER
            customer_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
    responses:
      200:
        description: User updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: User updated successfully
      400:
        description: Validation error
      404:
        description: User not found
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        try:
            uuid.UUID(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for user_id'})

        connection = get_db_connection()
        cursor = connection.cursor()

        updates = []
        params = []

        if 'username' in data:
            updates.append("username = %s")
            params.append(data['username'])

        if 'password' in data:
            updates.append("password = %s")
            params.append(generate_password_hash(data['password']))

        if 'role' in data and data['role'] in ['ADMIN', 'USER']:
            updates.append("role = %s")
            params.append(data['role'])

        if 'customer_id' in data:
            updates.append("customer_id = %s")
            params.append(data['customer_id'])

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(user_id)
        query = f"UPDATE user SET {', '.join(updates)} WHERE user_id = %s"
        cursor.execute(query, tuple(params))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "User not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# delete a user
@user_blueprint.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    Delete a user
    ---
    tags:
      - Users
    security:
      - BearerAuth: []    
    parameters:
      - name: user_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174000
    responses:
      200:
        description: User deleted successfully
      404:
        description: User not found
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for user_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "User not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
