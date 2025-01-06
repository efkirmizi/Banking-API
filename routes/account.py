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
    """
    Create a new account
    ---
    tags:
      - Accounts
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            customer_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            account_type:
              type: string
              enum: [CHECKING, SAVINGS]
              example: SAVINGS
            branch_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174001
    responses:
      201:
        description: Account created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Account created successfully
            account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174002
      400:
        description: Validation error
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """
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
    """
    Get all accounts
    ---
    tags:
      - Accounts
    responses:
      200:
        description: List of accounts
        schema:
          type: array
          items:
            type: object
            properties:
              account_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174002
              customer_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174000
              account_type:
                type: string
                example: SAVINGS
              balance:
                type: number
                example: 500.75
              creation_date:
                type: string
                example: 2024-01-05T12:00:00
              branch_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174001
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """
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
    """
    Get a specific account by ID
    ---
    tags:
      - Accounts
    parameters:
      - name: account_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174002
    responses:
      200:
        description: Account details
        schema:
          type: object
          properties:
            account_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174002
            customer_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            account_type:
              type: string
              example: SAVINGS
            balance:
              type: number
              example: 500.75
            creation_date:
              type: string
              example: 2024-01-05T12:00:00
            branch_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174001
      404:
        description: Account not found
      403:
        description: Access forbidden (Admin only)
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
    """
    Update the balance of an account
    ---
    tags:
      - Accounts
    parameters:
      - name: account_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174002
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            amount:
              type: number
              example: 200.50
    responses:
      200:
        description: Account balance updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Account balance updated successfully
            new_balance:
              type: number
              example: 700.25
      400:
        description: Validation error (e.g., insufficient funds)
      404:
        description: Account not found
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """
    data = request.get_json()

    try:
        # Validate UUID
        try:
            uuid.UUID(account_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID format for account_id'}), 400

        # Validate input data
        if 'amount' not in data:
            return jsonify({"error": "Amount is required"}), 400

        amount = data.get('amount')
        if not isinstance(amount, (int, float)):
            return jsonify({"error": "Amount must be a numeric value"}), 400

        # Ensure amount is a float
        amount = float(amount)

        connection = get_db_connection()
        cursor = connection.cursor()

        # Get current balance
        cursor.execute("SELECT balance FROM account WHERE account_id = %s", (account_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "Account not found"}), 404

        # Convert current balance to float
        current_balance = float(result['balance'])

        # Calculate new balance
        new_balance = current_balance + amount

        # Ensure balance remains non-negative
        if new_balance < 0:
            return jsonify({"error": "Insufficient funds"}), 400

        # Update balance
        cursor.execute("UPDATE account SET balance = %s WHERE account_id = %s", (new_balance, account_id))
        connection.commit()

        return jsonify({"message": "Account balance updated successfully", "new_balance": new_balance}), 200

    except Exception as e:
        # Log the exception for debugging
        print(f"Error updating account balance: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Ensure connection and cursor are closed
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

# Delete an account
@account_blueprint.route('/accounts/<account_id>', methods=['DELETE'])
@admin_required
def delete_account(account_id):
    """
    Delete an account
    ---
    tags:
      - Accounts
    parameters:
      - name: account_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174002
    responses:
      200:
        description: Account deleted successfully
      404:
        description: Account not found
      403:
        description: Access forbidden (Admin only)
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
      cursor.execute("DELETE FROM account WHERE account_id = %s", (account_id,))
      connection.commit()

      if cursor.rowcount == 0:
        return jsonify({"error": "Account not found"}), 404

      cursor.close()
      connection.close()

      return jsonify({"message": "Account deleted successfully"}), 200

    except Exception as e:
      return jsonify({"error": str(e)}), 500