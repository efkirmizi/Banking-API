from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from datetime import datetime
from database import get_db_connection
from .admin import admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity

transaction_blueprint = Blueprint('transaction', __name__)

# Create a new transaction
@transaction_blueprint.route('/transactions', methods=['POST'])
@admin_required
def create_transaction():
    """
    Create a new transaction
    ---
    tags:
      - Transactions
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            from_account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174002
            to_account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            amount:
              type: number
              example: 250.75
            transaction_type:
              type: string
              enum: [TRANSFER, WITHDRAWAL, DEPOSIT]
              example: TRANSFER
    responses:
      201:
        description: Transaction created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Transaction created successfully
            transaction_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174004
      400:
        description: Validation error
      404:
        description: Account not found
      500:
        description: Internal server error
    """
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
    """
    Get all transactions
    ---
    tags:
      - Transactions
    responses:
      200:
        description: List of transactions
        schema:
          type: array
          items:
            type: object
            properties:
              transaction_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174004
              sender_account_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174002
              receiver_account_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174003
              amount:
                type: number
                example: 250.75
              transaction_type:
                type: string
                example: TRANSFER
              transaction_date:
                type: string
                example: 2024-01-05T12:00:00
      500:
        description: Internal server error
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
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
    """
    Get all transactions for a specific account
    ---
    tags:
      - Transactions
    parameters:
      - name: account_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174002
    responses:
      200:
        description: List of transactions for the account
        schema:
          type: array
          items:
            type: object
            properties:
              transaction_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174004
              sender_account_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174002
              receiver_account_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174003
              amount:
                type: number
                example: 250.75
              transaction_type:
                type: string
                example: TRANSFER
              transaction_date:
                type: string
                example: 2024-01-05T12:00:00
      404:
        description: Account not found
      500:
        description: Internal server error
    """
    try:
        try:
            uuid.UUID(account_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for account_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
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
    """
    Get a specific transaction by ID
    ---
    tags:
      - Transactions
    parameters:
      - name: transaction_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174004
    responses:
      200:
        description: Transaction details
        schema:
          type: object
          properties:
            transaction_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174004
            sender_account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174002
            receiver_account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            amount:
              type: number
              example: 250.75
            transaction_type:
              type: string
              example: TRANSFER
            transaction_date:
              type: string
              example: 2024-01-05T12:00:00
      404:
        description: Transaction not found
      500:
        description: Internal server error
    """
    try:
        try:
            uuid.UUID(transaction_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for transaction_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
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
    """
    Delete a specific transaction by ID
    ---
    tags:
      - Transactions
    parameters:
      - name: transaction_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174004
    responses:
      200:
        description: Transaction deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Transaction deleted successfully
      404:
        description: Transaction not found
      400:
        description: Invalid UUID string for transaction_id
      500:
        description: Internal server error
    """
    try:
        try:
            uuid.UUID(transaction_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for transaction_id'})

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
    
def get_customers_with_high_transactions(min_transaction_total):
    """
    Get customers with high transaction totals
    ---
    tags:
      - Transactions
    parameters:
      - name: min_transaction_total
        in: query
        required: false
        type: number
        default: 10000
        example: 15000
    responses:
      200:
        description: List of customers with high transaction totals
        schema:
          type: array
          items:
            type: object
            properties:
              customer_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174000
              first_name:
                type: string
                example: John
              last_name:
                type: string
                example: Doe
              total_transaction:
                type: number
                example: 50000.75
      404:
        description: No customers found exceeding the specified amount
      500:
        description: Internal server error
    """    
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        SELECT C.customer_id, C.first_name, C.last_name, SUM(T.amount) AS total_transaction
        FROM customer C
        JOIN account A ON C.customer_id = A.customer_id
        JOIN transaction T ON A.account_id = T.from_account_id OR A.account_id = T.to_account_id
        GROUP BY C.customer_id, C.first_name, C.last_name
        HAVING SUM(T.amount) > %s;
        """
        cursor.execute(query, (min_transaction_total,))
        results = cursor.fetchall()
        return results

    except Exception as e:
        raise RuntimeError(f"Database query failed: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@transaction_blueprint.route('/high_transactions/<min_transaction_total>', methods=['GET'])
@admin_required
def api_customers_high_transactions(min_transaction_total):
    """
    Fetch customers with high transaction totals
    ---
    tags:
      - Transactions
    parameters:
      - name: min_transaction_total
        in: query
        required: false
        type: number
        default: 10000
        example: 15000
    responses:
      200:
        description: List of customers with high transaction totals
        schema:
          type: array
          items:
            type: object
            properties:
              customer_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174000
              first_name:
                type: string
                example: John
              last_name:
                type: string
                example: Doe
              total_transaction:
                type: number
                example: 50000.75
      404:
        description: No customers found exceeding the specified amount
      500:
        description: Internal server error
    """
    try:
        results = get_customers_with_high_transactions(min_transaction_total)
        if not results:
            return jsonify({'message': 'No customers found with transactions exceeding the specified amount.'}), 404
        return jsonify(results), 200

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.', 'details': str(e)}), 500

@transaction_blueprint.route('/money_transfer', methods=['POST'])
@jwt_required()
def money_transfer():
    """
    Transfer money between accounts
    ---
    tags:
      - Transactions
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            sender_account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174002
            receiver_account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            amount:
              type: number
              example: 200.75
    responses:
      201:
        description: Money transfer successful
        schema:
          type: object
          properties:
            transaction_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174004
            sender_account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174002
            receiver_account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            amount:
              type: number
              example: 200.75
            message:
              type: string
              example: Money transfer is successful
      400:
        description: Validation error (e.g., insufficient balance or missing fields)
      403:
        description: Access denied
      404:
        description: Account not found
      500:
        description: Internal server error
    """
    user_id = get_jwt_identity()

    try:
        # Connect to DB
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch user and validate
        cursor.execute("SELECT customer_id FROM user WHERE user_id = %s", (user_id,))
        customer_id = cursor.fetchone()
        if not customer_id:
            return jsonify({'error': 'No customer associated with this user ID'}), 404

        data = request.get_json()
        sender_account_id = data.get('sender_account_id')
        receiver_account_id = data.get('receiver_account_id')
        amount = data.get('amount')

        # Validate input fields
        if not sender_account_id or not receiver_account_id or amount is None:
            return jsonify({'error': 'All fields are required'}), 400
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400

        # Check sender account
        cursor.execute("SELECT customer_id, balance FROM account WHERE account_id = %s", (sender_account_id,))
        sender_account = cursor.fetchone()
        if not sender_account or sender_account['customer_id'] != customer_id['customer_id']:
            return jsonify({'error': 'Invalid sender account or insufficient permissions'}), 403

        # Check receiver account
        cursor.execute("SELECT * FROM account WHERE account_id = %s", (receiver_account_id,))
        receiver_account = cursor.fetchone()
        if not receiver_account:
            return jsonify({'error': 'Receiver account not found'}), 404

        # Balance check
        if float(sender_account['balance']) < float(amount):
            return jsonify({'error': 'Insufficient balance'}), 400

        # Process transfer
        cursor.execute("UPDATE account SET balance = balance - %s WHERE account_id = %s", (amount, sender_account_id))
        cursor.execute("UPDATE account SET balance = balance + %s WHERE account_id = %s", (amount, receiver_account_id))

        # Record transaction
        transaction_id = str(uuid.uuid4())
        transaction_timestamp = datetime.now()
        cursor.execute("""
            INSERT INTO transaction (transaction_id, from_account_id, to_account_id, transaction_type, amount, transaction_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (transaction_id, sender_account_id, receiver_account_id, 'TRANSFER', amount, transaction_timestamp))

        connection.commit()

        return jsonify({
            'message': 'Money transfer is successful',
            'transaction_id': transaction_id,
            'sender_account_id': sender_account_id,
            'receiver_account_id': receiver_account_id,
            'amount': float(amount)
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()