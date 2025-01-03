from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from datetime import datetime
from database import get_db_connection
from .admin import admin_required

account_blueprint = Blueprint('account', __name__)

# Create a new account
@account_blueprint.route('/accounts', methods=['POST'])
@admin_required
def create_account():
    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['customer_id', 'account_type', 'branch_id']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate account type
        valid_account_types = ['CHECKING', 'SAVINGS']
        if data['account_type'] not in valid_account_types:
            raise BadRequest(f"Invalid account type. Valid types are: {', '.join(valid_account_types)}")

        # Generate unique account ID
        account_id = str(uuid.uuid4())

        # Get current date and time
        creation_date = datetime.now()

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
        INSERT INTO account (account_id, customer_id, account_type, balance, creation_date, branch_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
        account_id,
        data['customer_id'],
        data['account_type'],
        0.00,  # Default balance
        creation_date,
        data['branch_id'],
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Account created successfully", "account_id": account_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all accounts
@account_blueprint.route('/accounts', methods=['GET'])
@admin_required
def get_accounts():
  try:
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM account")
    accounts = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(accounts), 200

  except Exception as e:
    return jsonify({"error": str(e)}), 500

# Get a specific account by ID
@account_blueprint.route('/accounts/<account_id>', methods=['GET'])
@admin_required
def get_account(account_id):
  try:
    try:
      uuid.UUID(account_id)
    except ValueError:
      return jsonify({'error': 'Invalid UUID string for account_id'})
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM account WHERE account_id = %s", (account_id,))
    account = cursor.fetchone()
    cursor.close()
    connection.close()

    if not account:
      return jsonify({"error": "Account not found"}), 404

    return jsonify(account), 200

  except Exception as e:
    return jsonify({"error": str(e)}), 500

# Update an account (Note: Only balance updates are implemented here for simplicity)
@account_blueprint.route('/accounts/<account_id>/balance', methods=['PUT'])
@admin_required
def update_account_balance(account_id):
  data = request.get_json()
  try:
    try:
      uuid.UUID(account_id)
    except ValueError:
      return jsonify({'error': 'Invalid UUID string for account_id'})

    if 'amount' not in data:
      return jsonify({"error": "Amount is required"}), 400

    amount = data['amount']

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get current balance
    cursor.execute("SELECT balance FROM account WHERE account_id = %s", (account_id,))
    result = cursor.fetchone()
    if not result:
      return jsonify({"error": "Account not found"}), 404
    current_balance = result[0]

    # Calculate new balance
    new_balance = current_balance + amount

    # Ensure balance remains non-negative
    if new_balance < 0:
      return jsonify({"error": "Insufficient funds"}), 400

    # Update balance
    cursor.execute("UPDATE account SET balance = %s WHERE account_id = %s", (new_balance, account_id))
    connection.commit()

    # Close connection and cursor
    cursor.close()
    connection.close()

    return jsonify({"message": "Account balance updated successfully", "new_balance": new_balance}), 200

  except Exception as e:
    return jsonify({"error": str(e)}), 500

# Delete an account (Note: Account deletion might have business implications, handle with care)
@account_blueprint.route('/accounts/<account_id>', methods=['DELETE'])
@admin_required
def delete_account(account_id):
    try:
      try:
        uuid.UUID(account_id)
      except ValueError:
       return jsonify({'error': 'Invalid UUID string for account_id'})

      connection = get_db_connection()
      cursor = connection.cursor()
      cursor.execute("DELETE FROM account WHERE account_id = %s", (account_id,))
      connection.commit()

      if cursor.rowcount == 0:
        return jsonify({"error": "Account not found"}), 404

      cursor.close()
      connection.close()

      return jsonify({"message": "Account deleted successfully"}), 200

    except Exception as e:
      return jsonify({"error": str(e)}), 500