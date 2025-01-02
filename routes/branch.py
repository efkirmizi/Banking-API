from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from database import get_db_connection
from admin import admin_required

branch_blueprint = Blueprint('branch', __name__)

# Create a new branch
@branch_blueprint.route('/branches', methods=['POST'])
@admin_required
def create_branch():
    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['branch_name', 'address_line1', 'city', 'zip_code', 'phone_number']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Generate unique branch ID
        branch_id = str(uuid.uuid4())

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
        INSERT INTO branch (branch_id, branch_name, address_line1, address_line2, city, zip_code, phone_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
        branch_id,
        data['branch_name'],
        data['address_line1'],
        data.get('address_line2', None),  # Optional field
        data['city'],
        data['zip_code'],
        data['phone_number'],
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Branch created successfully", "branch_id": branch_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all branches
@branch_blueprint.route('/branches', methods=['GET'])
@admin_required
def get_branches():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM branch")
        branches = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(branches), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific branch by ID
@branch_blueprint.route('/branches/<branch_id>', methods=['GET'])
@admin_required
def get_branch(branch_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM branch WHERE branch_id = %s", (branch_id,))
        branch = cursor.fetchone()
        cursor.close()
        connection.close()

        if not branch:
            return jsonify({"error": "Branch not found"}), 404

        return jsonify(branch), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a branch
@branch_blueprint.route('/branches/<branch_id>', methods=['PUT'])
@admin_required
def update_branch(branch_id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare update statements
        updates = []
        params = []
        if 'branch_name' in data:
            updates.append("branch_name = %s")
            params.append(data['branch_name'])
        if 'address_line1' in data:
            updates.append("address_line1 = %s")
            params.append(data['address_line1'])
        if 'address_line2' in data:
            updates.append("address_line2 = %s")
            params.append(data['address_line2'])
        if 'city' in data:
            updates.append("city = %s")
            params.append(data['city'])
        if 'zip_code' in data:
            updates.append("zip_code = %s")
            params.append(data['zip_code'])
        if 'phone_number' in data:
            updates.append("phone_number = %s")
            params.append(data['phone_number'])

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        # Add branch_id to the end of the params list
        params.append(branch_id)

        # Construct the SQL UPDATE query
        query = f"UPDATE branch SET {', '.join(updates)} WHERE branch_id = %s"

        # Execute the query and commit changes
        cursor.execute(query, tuple(params))
        connection.commit()

        # Check if any rows were affected
        if cursor.rowcount == 0:
            return jsonify({"error": "Branch not found"}), 404

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Branch updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a branch
@branch_blueprint.route('/branches/<branch_id>', methods=['DELETE'])
@admin_required
def delete_branch(branch_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM branch WHERE branch_id = %s", (branch_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Branch not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Branch deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500