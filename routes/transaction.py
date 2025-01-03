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
    Fetch customers who made transactions totaling more than a specified amount.

    :param min_transaction_total: Minimum transaction total required.
    :return: List of dictionaries containing customer details and total transaction amounts.
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


@transaction_blueprint.route('/high_transactions', methods=['GET'])
@admin_required
def api_customers_high_transactions():
    """
    API endpoint to fetch customers who made transactions totaling more than a specified amount.
    """
    min_transaction_total = request.args.get('min_transaction_total', type=float, default=10000)

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
    user_id = get_jwt_identity()

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT customer_id FROM user WHERE user_id = %s", (user_id,))
        customer_id_row = cursor.fetchone()
        if not customer_id_row:
            return jsonify({'error': 'customer_id is None'}), 404
        customer_id = customer_id_row['customer_id']

        cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
        sender_customer = cursor.fetchone()
        if not sender_customer:
            return jsonify({'error': 'No customer exists with this customer_id'}), 404

        data = request.get_json()
        sender_account_id = data.get('sender_account_id')
        receiver_account_id = data.get('receiver_account_id')
        amount = data.get('amount')

        if not sender_account_id or not receiver_account_id or not amount:
            return jsonify({'error': 'All fields are required: sender_account_id, receiver_account_id, amount'}), 400

        try:
            uuid.UUID(sender_account_id)
            uuid.UUID(receiver_account_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID format'}), 400

        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400

        cursor.execute("SELECT * FROM account WHERE account_id = %s", (sender_account_id,))
        sender_account = cursor.fetchone()
        if not sender_account:
            return jsonify({'error': 'No account exists with this account_id sender'}), 404

        if sender_account['customer_id'] != customer_id:
            return jsonify({'error': 'Access denied: This account is not connected with claimed customer_id'}), 403

        cursor.execute("SELECT * FROM account WHERE account_id = %s", (receiver_account_id,))
        receiver_account = cursor.fetchone()
        if not receiver_account:
            return jsonify({'error': 'No account exists with this account_id receiver'}), 404

        if sender_account['balance'] < amount:
            return jsonify({'error': 'Insufficient balance'}), 400

        cursor.execute("UPDATE account SET balance = balance - %s WHERE account_id = %s", (amount, sender_account_id))
        cursor.execute("UPDATE account SET balance = balance + %s WHERE account_id = %s", (amount, receiver_account_id))

        transaction_timestamp = datetime.now()
        cursor.execute("""
            INSERT INTO Transaction (
                from_account_id, to_account_id, transaction_type, amount, transaction_timestamp
            ) VALUES (
                %s, %s, %s, %s, %s
            )
        """, (sender_account_id, receiver_account_id, 'TRANSFER', amount, transaction_timestamp))

        connection.commit()

        return jsonify({
            'message': 'Money transfer is successful',
            'sender_account_id': sender_account_id,
            'receiver_account_id': receiver_account_id,
            'transaction_type': 'TRANSFER',
            'amount': amount,
            'transaction_timestamp': transaction_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }), 201

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()