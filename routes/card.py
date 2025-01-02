from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from datetime import date
from database import get_db_connection
from .admin import admin_required

card_blueprint = Blueprint('card', __name__)

# Create a new card
@card_blueprint.route('/cards', methods=['POST'])
@admin_required
def create_card():
    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['account_id', 'card_type', 'card_number', 'expiration_date', 'cvv']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate card type
        valid_card_types = ['DEBIT', 'CREDIT']
        if data['card_type'] not in valid_card_types:
            raise BadRequest(f"Invalid card type. Valid types are: {', '.join(valid_card_types)}")

        # Validate expiration date (basic check)
        try:
            expiration_date = date.fromisoformat(data['expiration_date'])
        except ValueError:
            raise BadRequest("Invalid expiration date format. Use YYYY-MM-DD.")

        # Generate unique card ID
        card_id = str(uuid.uuid4())

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
        INSERT INTO card (card_id, account_id, card_type, card_number, expiration_date, cvv, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
        """
        params = (
        card_id,
        data['account_id'],
        data['card_type'],
        data['card_number'],
        expiration_date,
        data['cvv'],
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Card created successfully", "card_id": card_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all cards
@card_blueprint.route('/cards', methods=['GET'])
@admin_required
def get_cards():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM card")
        cards = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(cards), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific card by ID
@card_blueprint.route('/cards/<card_id>', methods=['GET'])
@admin_required
def get_card(card_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM card WHERE card_id = %s", (card_id,))
        card = cursor.fetchone()
        cursor.close()
        connection.close()

        if not card:
            return jsonify({"error": "Card not found"}), 404

        return jsonify(card), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update card status (e.g., 'BLOCKED', 'EXPIRED')
@card_blueprint.route('/cards/<card_id>/status', methods=['PUT'])
@admin_required
def update_card_status(card_id):
    data = request.get_json()
    try:
        if 'status' not in data:
            return jsonify({"error": "Status is required"}), 400

        valid_statuses = ['ACTIVE', 'BLOCKED', 'EXPIRED']
        if data['status'] not in valid_statuses:
            return jsonify({"error": "Invalid status. Valid statuses are: {', '.join(valid_statuses)}"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("UPDATE card SET status = %s WHERE card_id = %s", (data['status'], card_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Card not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Card status updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a card (Note: Card deletion might have business implications, handle with care)
@card_blueprint.route('/cards/<card_id>', methods=['DELETE'])
@admin_required
def delete_card(card_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM card WHERE card_id = %s", (card_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Card not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Card deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500