from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from datetime import datetime
from database import get_db_connection
from admin import admin_required

transaction_blueprint = Blueprint('transaction', __name__)

# Create a new transaction
@transaction_blueprint.route('/transactions', methods=['POST'])
@admin_required
def create_transaction():
    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['from_account_id', 'transaction_type', 'amount']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate transaction type
        valid_transaction_types = ['DEPOSIT', 'WITHDRAWAL', 'TRANSFER']
        if data['transaction_type'] not in valid_transaction_types:
            raise BadRequest(f"Invalid transaction type. Valid types are: {', '.join(valid_transaction_types)}")

        # Get current timestamp
        transaction_timestamp = datetime.now()

        # Handle different transaction types
        if data['transaction_type'] == 'TRANSFER':
            if 'to_account_id' not in data:
                raise BadRequest("To account ID is required for transfers.")

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())

        # Prepare SQL query
        query = """
        INSERT INTO transaction (transaction_id, from_account_id, to_account_id, transaction_type, amount, transaction_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
        transaction_id,
        data['from_account_id'],
        data.get('to_account_id', None),  # Set to_account_id to None for deposits and withdrawals
        data['transaction_type'],
        data['amount'],
        transaction_timestamp,
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Transaction created successfully", "transaction_id": transaction_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all transactions
@transaction_blueprint.route('/transactions', methods=['GET'])
@admin_required
def get_transactions():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transaction")
        transactions = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(transactions), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get transactions for a specific account
@transaction_blueprint.route('/accounts/<account_id>/transactions', methods=['GET'])
@admin_required
def get_account_transactions(account_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
        SELECT * FROM transaction 
        WHERE from_account_id = %s OR to_account_id = %s
        """, (account_id, account_id))
        transactions = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(transactions), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific transaction by ID
@transaction_blueprint.route('/transactions/<transaction_id>', methods=['GET'])
@admin_required
def get_transaction(transaction_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transaction WHERE transaction_id = %s", (transaction_id,))
        transaction = cursor.fetchone()
        cursor.close()
        connection.close()

        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        return jsonify(transaction), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a transaction (Note: Transaction deletion might have business implications, handle with care)
@transaction_blueprint.route('/transactions/<transaction_id>', methods=['DELETE'])
@admin_required
def delete_transaction(transaction_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM transaction WHERE transaction_id = %s", (transaction_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Transaction not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Transaction deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500