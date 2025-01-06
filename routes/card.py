from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from datetime import date
from database import get_db_connection
from .admin import admin_required
import re

card_blueprint = Blueprint('card', __name__)

# Create a new card
@card_blueprint.route('/cards', methods=['POST'])
@admin_required
def create_card():
    """
    Create a new card
    ---
    tags:
      - Cards
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            card_type:
              type: string
              example: DEBIT
              enum: [DEBIT, CREDIT]
            card_number:
              type: string
              example: 1234-5678-9012-3456
            expiration_date:
              type: string
              format: date
              example: 2025-12-31
            cvv:
              type: string
              example: 123
    responses:
      201:
        description: Card created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Card created successfully
            card_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174001
      400:
        description: Validation error
      500:
        description: Internal server error
    """

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

        card_number = data['card_number']
        sanitized_card_number = re.sub(r"[^0-9-]", "", card_number) 

        # Prepare SQL query
        query = """
        INSERT INTO card (card_id, account_id, card_type, card_number, expiration_date, cvv, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
        """
        params = (
        card_id,
        data['account_id'],
        data['card_type'],
        sanitized_card_number,
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
    """
    Get all cards
    ---
    tags:
      - Cards
    responses:
      200:
        description: List of all cards
        schema:
          type: array
          items:
            type: object
            properties:
              card_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174001
              account_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174000
              card_type:
                type: string
                example: DEBIT
              card_number:
                type: string
                example: 1234-5678-9012-3456
              expiration_date:
                type: string
                example: 2025-12-31
              cvv:
                type: string
                example: 123
              status:
                type: string
                example: ACTIVE
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
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
    """
    Get a specific card by ID
    ---
    tags:
      - Cards
    parameters:
      - name: card_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174001
    responses:
      200:
        description: Card details
        schema:
          type: object
          properties:
            card_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174001
            account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            card_type:
              type: string
              example: DEBIT
            card_number:
              type: string
              example: 1234-5678-9012-3456
            expiration_date:
              type: string
              example: 2025-12-31
            cvv:
              type: string
              example: 123
            status:
              type: string
              example: ACTIVE
      404:
        description: Card not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(card_id)
        except ValueError:
            return jsonify({'error': 'Invalid card_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
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
    """
    Update the status of a card
    ---
    tags:
      - Cards
    parameters:
      - name: card_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174001
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              example: BLOCKED
              enum: [ACTIVE, BLOCKED, EXPIRED]
    responses:
      200:
        description: Card status updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Card status updated successfully
      400:
        description: Validation error
      404:
        description: Card not found
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        try:
            uuid.UUID(card_id)
        except ValueError:
            return jsonify({'error': 'Invalid card_id'})

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
    """
    Delete a card
    ---
    tags:
      - Cards
    parameters:
      - name: card_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174001
    responses:
      200:
        description: Card deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Card deleted successfully
      404:
        description: Card not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(card_id)
        except ValueError:
            return jsonify({'error': 'Invalid card_id'})

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