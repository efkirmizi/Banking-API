from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from database import get_db_connection
from .admin import admin_required

branch_blueprint = Blueprint('branch', __name__)

# Create a new branch
@branch_blueprint.route('/branches', methods=['POST'])
@admin_required
def create_branch():
    """
    Create a new branch
    ---
    tags:
      - Branches
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            branch_name:
              type: string
              example: ITU Branch
            address_line1:
              type: string
              example: Katar cd.
            address_line2:
              type: string
              example: No 4
              nullable: true
            city:
              type: string
              example: IST
            zip_code:
              type: string
              example: 54321
            phone_number:
              type: string
              example: 1234567890
    responses:
      201:
        description: Branch created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Branch created successfully
            branch_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
      400:
        description: Validation error
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['branch_name', 'address_line1', 'city', 'zip_code', 'phone_number']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Generate unique branch ID
        branch_id = str(uuid.uuid4())

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
        INSERT INTO branch (branch_id, branch_name, address_line1, address_line2, city, zip_code, phone_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
        branch_id,
        data['branch_name'],
        data['address_line1'],
        data.get('address_line2', None),  # Optional field
        data['city'],
        data['zip_code'],
        data['phone_number'],
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Branch created successfully", "branch_id": branch_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all branches
@branch_blueprint.route('/branches', methods=['GET'])
@admin_required
def get_branches():
    """
    Get all branches
    ---
    tags:
      - Branches
    responses:
      200:
        description: List of all branches
        schema:
          type: array
          items:
            type: object
            properties:
              branch_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174000
              branch_name:
                type: string
                example: Istinye Branch
              address_line1:
                type: string
                example: Katar cd.
              address_line2:
                type: string
                example: no 4
              city:
                type: string
                example: istanbul
              zip_code:
                type: string
                example: 54321
              phone_number:
                type: string
                example: 1234567890
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM branch")
        branches = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(branches), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific branch by ID
@branch_blueprint.route('/branches/<branch_id>', methods=['GET'])
@admin_required
def get_branch(branch_id):
    """
    Get a specific branch by ID
    ---
    tags:
      - Branches
    parameters:
      - name: branch_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174000
    responses:
      200:
        description: Branch details
        schema:
          type: object
          properties:
            branch_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            branch_name:
              type: string
              example: aaa Branch
            address_line1:
              type: string
              example: 123 cd.
            address_line2:
              type: string
              example: 321 sk.
            city:
              type: string
              example: istanbul
            zip_code:
              type: string
              example: 54321
            phone_number:
              type: string
              example: 1234567890
      404:
        description: Branch not found
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM branch WHERE branch_id = %s", (branch_id,))
        branch = cursor.fetchone()
        cursor.close()
        connection.close()

        if not branch:
            return jsonify({"error": "Branch not found"}), 404

        return jsonify(branch), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a branch
@branch_blueprint.route('/branches/<branch_id>', methods=['PUT'])
@admin_required
def update_branch(branch_id):
    """
    Update branch details
    ---
    tags:
      - Branches
    parameters:
      - name: branch_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174000
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            branch_name:
              type: string
              example: aaa Branch
            address_line1:
              type: string
              example: ee cd.
            address_line2:
              type: string
              example: no 4
            city:
              type: string
              example: artvin
            zip_code:
              type: string
              example: 67890
            phone_number:
              type: string
              example: 9876543210
    responses:
      200:
        description: Branch updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Branch updated successfully
      400:
        description: Validation error
      404:
        description: Branch not found
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare update statements
        updates = []
        params = []
        if 'branch_name' in data:
            updates.append("branch_name = %s")
            params.append(data['branch_name'])
        if 'address_line1' in data:
            updates.append("address_line1 = %s")
            params.append(data['address_line1'])
        if 'address_line2' in data:
            updates.append("address_line2 = %s")
            params.append(data['address_line2'])
        if 'city' in data:
            updates.append("city = %s")
            params.append(data['city'])
        if 'zip_code' in data:
            updates.append("zip_code = %s")
            params.append(data['zip_code'])
        if 'phone_number' in data:
            updates.append("phone_number = %s")
            params.append(data['phone_number'])

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        # Construct the SQL UPDATE query with a placeholder for the WHERE clause
        query = f"UPDATE branch SET {', '.join(updates)} WHERE branch_id = %s"

        # Add branch_id to the end of the params list
        params.append(branch_id)
        # Execute the query and commit changes
        
        cursor.execute(query, tuple(params))
        connection.commit()

        # Check if any rows were affected
        if cursor.rowcount == 0:
            return jsonify({"error": "Branch not found"}), 404

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Branch updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a branch
@branch_blueprint.route('/branches/<branch_id>', methods=['DELETE'])
@admin_required
def delete_branch(branch_id):
    """
    Delete a branch
    ---
    tags:
      - Branches
    parameters:
      - name: branch_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174000
    responses:
      200:
        description: Branch deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Branch deleted successfully
      404:
        description: Branch not found
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM branch WHERE branch_id = %s", (branch_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Branch not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Branch deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_branches_with_conditions(min_employees: int = 5, min_accounts: int = 3):
    """
    Get branches with specific conditions
    ---
    tags:
      - Branches
    parameters:
      - name: min_employees
        in: query
        required: false
        type: integer
        default: 5
        example: 10
      - name: min_accounts
        in: query
        required: false
        type: integer
        default: 3
        example: 5
    responses:
      200:
        description: List of branches meeting the criteria
        schema:
          type: array
          items:
            type: object
            properties:
              branch_name:
                type: string
                example: Downtown Branch
              employee_count:
                type: integer
                example: 12
              account_count:
                type: integer
                example: 7
      404:
        description: No branches found
      400:
        description: Invalid input values
      500:
        description: Internal server error
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        SELECT B.branch_name, 
               COUNT(DISTINCT E.employee_id) AS employee_count, 
               COUNT(DISTINCT A.account_id) AS account_count 
        FROM branch B 
        LEFT JOIN employee E ON B.branch_id = E.branch_id 
        LEFT JOIN account A ON B.branch_id = A.branch_id 
        GROUP BY B.branch_name
        HAVING COUNT(DISTINCT E.employee_id) > %s AND COUNT(DISTINCT A.account_id) >= %s;
        """
        cursor.execute(query, (min_employees, min_accounts))
        branches = cursor.fetchall()
        return branches

    except Exception as e:
        raise RuntimeError(f"Database query failed: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@branch_blueprint.route('/branches_with_conditions', methods=['GET'])
@admin_required
def api_branches_with_conditions():
    """
    Get branches with specific conditions
    ---
    tags:
      - Branches
    parameters:
      - name: min_employees
        in: query
        required: false
        type: integer
        default: 5
        example: 10
        description: Minimum number of employees required.
      - name: min_accounts
        in: query
        required: false
        type: integer
        default: 3
        example: 7
        description: Minimum number of accounts required.
    responses:
      200:
        description: List of branches meeting the specified criteria.
        schema:
          type: array
          items:
            type: object
            properties:
              branch_name:
                type: string
                example: Downtown Branch
              employee_count:
                type: integer
                example: 12
              account_count:
                type: integer
                example: 8
      404:
        description: No branches found matching the specified criteria.
      400:
        description: Invalid input values (e.g., negative integers).
        schema:
          type: object
          properties:
            error:
              type: string
              example: Minimum values must be non-negative integers.
      500:
        description: Internal server error or database query failure.
        schema:
          type: object
          properties:
            error:
              type: string
              example: An unexpected error occurred.
            details:
              type: string
              example: Database connection failed.
    """

    try:
        min_employees = request.args.get('min_employees', default=5, type=int)
        min_accounts = request.args.get('min_accounts', default=3, type=int)

        if min_employees < 0 or min_accounts < 0:
            return jsonify({'error': 'Minimum values must be non-negative integers.'}), 400

        results = get_branches_with_conditions(min_employees, min_accounts)

        if not results:
            return jsonify({'message': 'No branches found matching the specified criteria.'}), 404

        return jsonify(results), 200

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.', 'details': str(e)}), 500
