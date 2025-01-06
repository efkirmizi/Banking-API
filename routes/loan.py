from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from datetime import date
from database import get_db_connection
from .admin import admin_required

loan_blueprint = Blueprint('loan', __name__)

# Create a new loan
@loan_blueprint.route('/loans', methods=['POST'])
@admin_required
def create_loan():
    """
    Create a new loan
    ---
    tags:
      - Loans
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
            loan_type:
              type: string
              enum: [HOME, AUTO, PERSONAL]
              example: PERSONAL
            principal_amount:
              type: number
              example: 50000.00
            interest_rate:
              type: number
              example: 5.5
            start_date:
              type: string
              format: date
              example: 2024-01-01
            end_date:
              type: string
              format: date
              example: 2027-01-01
    responses:
      201:
        description: Loan created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Loan created successfully
            loan_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
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
        required_fields = ['customer_id', 'loan_type', 'principal_amount', 'interest_rate', 'start_date', 'end_date']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate customer_id
        try:
            uuid.UUID(data['customer_id'])
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for customer_id'})

        # Validate loan type
        valid_loan_types = ['HOME', 'AUTO', 'PERSONAL']
        if data['loan_type'] not in valid_loan_types:
            raise BadRequest(f"Invalid loan type. Valid types are: {', '.join(valid_loan_types)}")

        # Validate dates
        start_date = date.fromisoformat(data['start_date'])
        end_date = date.fromisoformat(data['end_date'])
        if start_date >= end_date:
            raise BadRequest("Start date must be before end date.")

        # Generate unique loan ID
        loan_id = str(uuid.uuid4())

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
        INSERT INTO loan (loan_id, customer_id, loan_type, principal_amount, interest_rate, start_date, end_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
        """
        params = (
        loan_id,
        data['customer_id'],
        data['loan_type'],
        data['principal_amount'],
        data['interest_rate'],
        start_date,
        end_date,
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Loan created successfully", "loan_id": loan_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all loans
@loan_blueprint.route('/loans', methods=['GET'])
@admin_required
def get_loans():
    """
    Get all loans
    ---
    tags:
      - Loans
    responses:
      200:
        description: List of loans
        schema:
          type: array
          items:
            type: object
            properties:
              loan_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174003
              customer_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174000
              loan_type:
                type: string
                example: PERSONAL
              principal_amount:
                type: number
                example: 50000.00
              interest_rate:
                type: number
                example: 5.5
              start_date:
                type: string
                format: date
                example: 2024-01-01
              end_date:
                type: string
                format: date
                example: 2027-01-01
              status:
                type: string
                example: ACTIVE
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM loan")
        loans = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(loans), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific loan by ID
@loan_blueprint.route('/loans/<loan_id>', methods=['GET'])
@admin_required
def get_loan(loan_id):
    """
    Get a specific loan by ID
    ---
    tags:
      - Loans
    parameters:
      - name: loan_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174003
    responses:
      200:
        description: Loan details
        schema:
          type: object
          properties:
            loan_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            customer_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            loan_type:
              type: string
              example: PERSONAL
            principal_amount:
              type: number
              example: 50000.00
            interest_rate:
              type: number
              example: 5.5
            start_date:
              type: string
              format: date
              example: 2024-01-01
            end_date:
              type: string
              format: date
              example: 2027-01-01
            status:
              type: string
              example: ACTIVE
      404:
        description: Loan not found
      403:
        description: Access forbidden (Admin only)
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
        cursor.execute("SELECT * FROM loan WHERE loan_id = %s", (loan_id,))
        loan = cursor.fetchone()
        cursor.close()
        connection.close()

        if not loan:
            return jsonify({"error": "Loan not found"}), 404

        return jsonify(loan), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update loan status (e.g., 'PAID_OFF', 'DEFAULT')
@loan_blueprint.route('/loans/<loan_id>/status', methods=['PUT'])
@admin_required
def update_loan_status(loan_id):
    """
    Update the status of a loan
    ---
    tags:
      - Loans
    parameters:
      - name: loan_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174003
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              enum: [ACTIVE, PAID_OFF, DEFAULT]
              example: PAID_OFF
    responses:
      200:
        description: Loan status updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Loan status updated successfully
      400:
        description: Validation error
      404:
        description: Loan not found
      403:
        description: Access forbidden (Admin only)
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        try:
            uuid.UUID(loan_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for loan_id'})

        if 'status' not in data:
            return jsonify({"error": "Status is required"}), 400

        valid_statuses = ['ACTIVE', 'PAID_OFF', 'DEFAULT']
        if data['status'] not in valid_statuses:
            return jsonify({"error": "Invalid status. Valid statuses are: {', '.join(valid_statuses)}"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("UPDATE loan SET status = %s WHERE loan_id = %s", (data['status'], loan_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Loan not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Loan status updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a loan (Note: Loan deletion might have business implications, handle with care)
@loan_blueprint.route('/loans/<loan_id>', methods=['DELETE'])
@admin_required
def delete_loan(loan_id):
    """
    Delete a loan
    ---
    tags:
      - Loans
    parameters:
      - name: loan_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174003
    responses:
      200:
        description: Loan deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Loan deleted successfully
      404:
        description: Loan not found
      403:
        description: Access forbidden (Admin only)
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
        cursor.execute("DELETE FROM loan WHERE loan_id = %s", (loan_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Loan not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Loan deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500