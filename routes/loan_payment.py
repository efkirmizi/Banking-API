from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from datetime import datetime
from database import get_db_connection
from .admin import admin_required

loan_payment_blueprint = Blueprint('loan_payment', __name__)

# Create a new loan payment
@loan_payment_blueprint.route('/loan_payments', methods=['POST'])
@admin_required
def create_loan_payment():
    """
    Create a new loan payment
    ---
    tags:
      - Loan Payments
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            loan_id:
              type: string
              example: "123e4567-e89b-12d3-a456-426614174003"
            payment_amount:
              type: number
              example: 1000.50
    responses:
      201:
        description: Loan payment recorded successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Loan payment recorded successfully
            loan_payment_id:
              type: string
              example: "123e4567-e89b-12d3-a456-426614174005"
            remaining_balance:
              type: number
              example: 9000.50
            payment_date:
              type: string
              example: "2025-01-06T12:00:00"
      400:
        description: Validation error
      404:
        description: Loan not found
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['loan_id', 'payment_amount']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        try:
            uuid.UUID(data['loan_id'])
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for loan_id'})

        # Get current date and time
        payment_date = datetime.now()

        # Get loan details to calculate remaining balance
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT principal_amount FROM loan WHERE loan_id = %s", (data['loan_id'],))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Loan not found"}), 404
        principal_amount = result['principal_amount']

        # Calculate remaining balance
        remaining_balance = principal_amount - data['payment_amount']

        # Ensure remaining balance is not negative
        if remaining_balance < 0:
            raise BadRequest("Payment amount exceeds remaining principal.")

        # Generate unique loan payment ID
        loan_payment_id = str(uuid.uuid4())

        # Prepare SQL query
        query = """
        INSERT INTO loan_payment (loan_payment_id, loan_id, payment_date, payment_amount, remaining_balance)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (
        loan_payment_id,
        data['loan_id'],
        payment_date,
        data['payment_amount'],
        remaining_balance,
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Loan payment recorded successfully", "loan_payment_id": loan_payment_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all loan payments
@loan_payment_blueprint.route('/loan_payments', methods=['GET'])
@admin_required
def get_loan_payments():
    """
    Get all loan payments
    ---
    tags:
      - Loan Payments
    responses:
      200:
        description: List of all loan payments
        schema:
          type: array
          items:
            type: object
            properties:
              loan_payment_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174005
              loan_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174003
              payment_date:
                type: string
                example: 2024-01-05T12:00:00
              payment_amount:
                type: number
                example: 1000.50
              remaining_balance:
                type: number
                example: 9000.50
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM loan_payment")
        loan_payments = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(loan_payments), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get loan payments for a specific loan
@loan_payment_blueprint.route('/loans/<loan_id>/payments', methods=['GET'])
@admin_required
def get_loan_payments_by_loan(loan_id):
    """
    Get loan payments for a specific loan
    ---
    tags:
      - Loan Payments
    parameters:
      - name: loan_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174003
    responses:
      200:
        description: List of payments for the specified loan
        schema:
          type: array
          items:
            type: object
            properties:
              loan_payment_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174005
              loan_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174003
              payment_date:
                type: string
                example: 2024-01-05T12:00:00
              payment_amount:
                type: number
                example: 1000.50
              remaining_balance:
                type: number
                example: 9000.50
      404:
        description: Loan not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(loan_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for loan_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM loan_payment WHERE loan_id = %s", (loan_id,))
        loan_payments = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(loan_payments), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific loan payment by ID
@loan_payment_blueprint.route('/loan_payments/<loan_payment_id>', methods=['GET'])
@admin_required
def get_loan_payment(loan_payment_id):
    """
    Get a specific loan payment by ID
    ---
    tags:
      - Loan Payments
    parameters:
      - name: loan_payment_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174005
    responses:
      200:
        description: Loan payment details
        schema:
          type: object
          properties:
            loan_payment_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174005
            loan_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            payment_date:
              type: string
              example: 2024-01-05T12:00:00
            payment_amount:
              type: number
              example: 1000.50
            remaining_balance:
              type: number
              example: 9000.50
      404:
        description: Loan payment not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(loan_payment_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for loan_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM loan_payment WHERE loan_payment_id = %s", (loan_payment_id,))
        loan_payment = cursor.fetchone()
        cursor.close()
        connection.close()

        if not loan_payment:
            return jsonify({"error": "Loan payment not found"}), 404

        return jsonify(loan_payment), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# This endpoint is for demonstration purposes only and might need adjustments
# Update remaining balance (should be calculated and updated automatically)
# @loan_payment_blueprint.route('/loan_payments/<loan_payment_id>', methods=['PUT'])
# def update_loan_payment(loan_payment_id):
#   # ... (Implementation for updating remaining balance)

# Delete a loan payment (Note: Consider implications before deleting payment records)
@loan_payment_blueprint.route('/loan_payments/<loan_payment_id>', methods=['DELETE'])
@admin_required
def delete_loan_payment(loan_payment_id):
    """
    Delete a loan payment
    ---
    tags:
      - Loan Payments
    parameters:
      - name: loan_payment_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174005
    responses:
      200:
        description: Loan payment deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Loan payment deleted successfully
      404:
        description: Loan payment not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(loan_payment_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for loan_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM loan_payment WHERE loan_payment_id = %s", (loan_payment_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Loan payment not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Loan payment deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500