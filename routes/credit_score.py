from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from database import get_db_connection
from .admin import admin_required

credit_score_blueprint = Blueprint('credit_score', __name__)

# Create a new credit score
@credit_score_blueprint.route('/credit_scores', methods=['POST'])
@admin_required
def create_credit_score():
    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['customer_id', 'score', 'risk_category']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Generate unique credit score ID
        credit_score_id = str(uuid.uuid4())

        # Set computed_by_system to False by default
        computed_by_system = data.get('computed_by_system', False)

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
        INSERT INTO credit_score (credit_score_id, customer_id, score, risk_category, computed_by_system)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (
        credit_score_id,
        data['customer_id'],
        data['score'],
        data['risk_category'],
        computed_by_system,
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Credit score created successfully", "credit_score_id": credit_score_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all credit scores
@credit_score_blueprint.route('/credit_scores', methods=['GET'])
@admin_required
def get_credit_scores():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credit_score")
        credit_scores = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(credit_scores), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific credit score by ID
@credit_score_blueprint.route('/credit_scores/<credit_score_id>', methods=['GET'])
@admin_required
def get_credit_score(credit_score_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credit_score WHERE credit_score_id = %s", (credit_score_id,))
        credit_score = cursor.fetchone()
        cursor.close()
        connection.close()

        if not credit_score:
            return jsonify({"error": "Credit score not found"}), 404

        return jsonify(credit_score), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a credit score (consider constraints and potential security implications)
@credit_score_blueprint.route('/credit_scores/<credit_score_id>', methods=['PUT'])
@admin_required
def update_credit_score(credit_score_id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare update statements
        updates = []
        params = []
        if 'score' in data:
            updates.append("score = %s")
            params.append(data['score'])
        if 'risk_category' in data:
            updates.append("risk_category = %s")
            params.append(data['risk_category'])
        if 'computed_by_system' in data:
            updates.append("computed_by_system = %s")
            params.append(data['computed_by_system'])

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        # Add credit_score_id to the end of the params list
        params.append(credit_score_id)

        # Construct the SQL UPDATE query
        query = f"UPDATE credit_score SET {', '.join(updates)} WHERE credit_score_id = %s"

        # Execute the query and commit changes
        cursor.execute(query, tuple(params))
        connection.commit()

        # Check if any rows were affected
        if cursor.rowcount == 0:
            return jsonify({"error": "Credit score not found"}), 404

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Credit score updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a credit score (Note: Credit score deletion might have business implications, handle with care)
@credit_score_blueprint.route('/credit_scores/<credit_score_id>', methods=['DELETE'])
@admin_required
def delete_credit_score(credit_score_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM credit_score WHERE credit_score_id = %s", (credit_score_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Credit score not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Credit score deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500