from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
import uuid
from database import get_db_connection
from .admin import admin_required

user_blueprint = Blueprint('user', __name__)

# create a new user
@user_blueprint.route('/users', methods=['POST'])
def create_user():
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
    try:
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
    data = request.get_json()
    try:
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
    try:
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
