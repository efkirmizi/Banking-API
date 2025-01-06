from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid, re
from datetime import datetime
from database import get_db_connection
from .admin import admin_required

employee_blueprint = Blueprint('employee', __name__)

# Create a new employee
@employee_blueprint.route('/employees', methods=['POST'])
@admin_required
def create_employee():
    """
    Create a new employee
    ---
    tags:
      - Employees
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            branch_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            first_name:
              type: string
              example: hazar
            last_name:
              type: string
              example: sozer
            position:
              type: string
              example: Manager
            hire_date:
              type: string
              format: date
              example: 2024-01-01
            phone_number:
              type: string
              example: 1234567890
            email:
              type: string
              example: sozer@example.com
    responses:
      201:
        description: Employee created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Employee created successfully
            employee_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174004
      400:
        description: Validation error
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['branch_id', 'first_name', 'last_name', 'position', 'hire_date', 'phone_number', 'email']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")
        
        try:
            uuid.UUID(data['branch_id'])
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for branch_id'})

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            raise BadRequest("Invalid email format.")
        
        # Generate unique employee ID
        employee_id = str(uuid.uuid4())

        # Parse hire_date
        hire_date = datetime.fromisoformat(data['hire_date'])

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
        INSERT INTO employee (employee_id, branch_id, first_name, last_name, position, hire_date, phone_number, email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
        employee_id,
        data['branch_id'],
        data['first_name'],
        data['last_name'],
        data['position'],
        hire_date,
        data['phone_number'],
        data['email'],
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Employee created successfully", "employee_id": employee_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all employees
@employee_blueprint.route('/employees', methods=['GET'])
@admin_required
def get_employees():
    """
    Get all employees
    ---
    tags:
      - Employees
    responses:
      200:
        description: List of all employees
        schema:
          type: array
          items:
            type: object
            properties:
              employee_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174004
              branch_id:
                type: string
                example: 123e4567-e89b-12d3-a456-426614174003
              first_name:
                type: string
                example: talha
              last_name:
                type: string
                example: ucar
              position:
                type: string
                example: Manager
              hire_date:
                type: string
                example: 2024-01-01
              phone_number:
                type: string
                example: 1234567890
              email:
                type: string
                example: talha@example.com
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM employee")
        employees = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(employees), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific employee by ID
@employee_blueprint.route('/employees/<employee_id>', methods=['GET'])
@admin_required
def get_employee(employee_id):
    """
    Get a specific employee by ID
    ---
    tags:
      - Employees
    parameters:
      - name: employee_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174004
    responses:
      200:
        description: Employee details
        schema:
          type: object
          properties:
            employee_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174004
            branch_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            first_name:
              type: string
              example: ece
            last_name:
              type: string
              example: ada
            position:
              type: string
              example: Manager
            hire_date:
              type: string
              example: 2024-01-01
            phone_number:
              type: string
              example: 1234567890
            email:
              type: string
              example: ece@example.com
      404:
        description: Employee not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(employee_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for employee_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM employee WHERE employee_id = %s", (employee_id,))
        employee = cursor.fetchone()
        cursor.close()
        connection.close()

        if not employee:
            return jsonify({"error": "Employee not found"}), 404

        return jsonify(employee), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update an employee
@employee_blueprint.route('/employees/<employee_id>', methods=['PUT'])
@admin_required
def update_employee(employee_id):
    """
    Update an employee's details
    ---
    tags:
      - Employees
    parameters:
      - name: employee_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174004
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            branch_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174003
            first_name:
              type: string
              example: belinay
            last_name:
              type: string
              example: caliskan
            position:
              type: string
              example: Assistant Manager
            hire_date:
              type: string
              format: date
              example: 2025-01-01
            phone_number:
              type: string
              example: 9876543210
            email:
              type: string
              example: caliskan@example.com
    responses:
      200:
        description: Employee updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Employee updated successfully
      400:
        description: Validation error
      404:
        description: Employee not found
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        try:
            uuid.UUID(employee_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for employee_id'})

        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare update statements
        updates = []
        params = []
        if 'branch_id' in data:
            updates.append("branch_id = %s")
            params.append(data['branch_id'])
        if 'first_name' in data:
            updates.append("first_name = %s")
            params.append(data['first_name'])
        if 'last_name' in data:
            updates.append("last_name = %s")
            params.append(data['last_name'])
        if 'position' in data:
            updates.append("position = %s")
            params.append(data['position'])
        if 'hire_date' in data:
            updates.append("hire_date = %s")
            params.append(datetime.fromisoformat(data['hire_date']))
        if 'phone_number' in data:
            updates.append("phone_number = %s")
            params.append(data['phone_number'])
        if 'email' in data:
            updates.append("email = %s")
            params.append(data['email'])

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        # Add employee_id to the end of the params list
        params.append(employee_id)

        # Construct the SQL UPDATE query
        query = f"UPDATE employee SET {', '.join(updates)} WHERE employee_id = %s"

        # Execute the query and commit changes
        cursor.execute(query, tuple(params))
        connection.commit()

        # Check if any rows were affected
        if cursor.rowcount == 0:
            return jsonify({"error": "Employee not found"}), 404

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Employee updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete an employee
@employee_blueprint.route('/employees/<employee_id>', methods=['DELETE'])
@admin_required
def delete_employee(employee_id):
    """
    Delete an employee
    ---
    tags:
      - Employees
    parameters:
      - name: employee_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174004
    responses:
      200:
        description: Employee deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Employee deleted successfully
      404:
        description: Employee not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(employee_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for employee_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM employee WHERE employee_id = %s", (employee_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Employee not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Employee deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500