from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from database import get_db_connection
from .admin import admin_required

customer_blueprint = Blueprint('customer', __name__)

# create a new customer
@customer_blueprint.route('/customers', methods=['POST'])
@admin_required
def create_customer():
    """
    Create a new customer
    ---
    tags:
      - Customers
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            first_name:
              type: string
              example: faruk
            last_name:
              type: string
              example: oz
            date_of_birth:
              type: string
              format: date
              example: 1990-01-01
            phone_number:
              type: string
              example: 1234567890
            email:
              type: string
              example: deneme@example.com
            address_line1:
              type: string
              example: katar cd.
            address_line2:
              type: string
              example: Apartment 4
              nullable: true
            city:
              type: string
              example: istanbul
            zip_code:
              type: string
              example: 54321
            wage_declaration:
              type: number
              example: 50000.00
              nullable: true
    responses:
      201:
        description: Customer created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Customer created successfully
            customer_id:
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
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'phone_number', 'email', 'address_line1', 'city', 'zip_code']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Generate unique customer ID
        customer_id = str(uuid.uuid4())

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
            INSERT INTO customer (customer_id, first_name, last_name, date_of_birth, phone_number, email, address_line1, address_line2, city, zip_code, wage_declaration)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            customer_id,
            data['first_name'],
            data['last_name'],
            data['date_of_birth'],
            data['phone_number'],
            data['email'],
            data['address_line1'],
            data.get('address_line2', None),  # Optional field
            data['city'],
            data['zip_code'],
            data.get('wage_declaration', 0.0),  # Optional field with default value
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Customer created successfully", "customer_id": customer_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all customers
@customer_blueprint.route('/customers', methods=['GET'])
@admin_required
def get_customers():
    """
    Get all customers
    ---
    tags:
      - Customers
    responses:
      200:
        description: List of all customers
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
                example: faruk
              last_name:
                type: string
                example: oz
              date_of_birth:
                type: string
                example: 1990-01-01
              phone_number:
                type: string
                example: 1234567890
              email:
                type: string
                example: deneme@example.com
              address_line1:
                type: string
                example: katar cd
              address_line2:
                type: string
                example: Apartment 4
              city:
                type: string
                example: istanbul
              zip_code:
                type: string
                example: 54321
              wage_declaration:
                type: number
                example: 50000.00
      500:
        description: Internal server error
    """

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM customer")
        customers = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(customers), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific customer by ID
@customer_blueprint.route('/customers/<customer_id>', methods=['GET'])
@admin_required
def get_customer(customer_id):
    """
    Get a specific customer by ID
    ---
    tags:
      - Customers
    parameters:
      - name: customer_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174000
    responses:
      200:
        description: Customer details
        schema:
          type: object
          properties:
            customer_id:
              type: string
              example: 123e4567-e89b-12d3-a456-426614174000
            first_name:
              type: string
              example: faruk
            last_name:
              type: string
              example: oz
            date_of_birth:
              type: string
              example: 1990-01-01
            phone_number:
              type: string
              example: 1234567890
            email:
              type: string
              example: deneme@example.com
            address_line1:
              type: string
              example: katar cd
            address_line2:
              type: string
              example: Apartment 4
            city:
              type: string
              example: istanbul
            zip_code:
              type: string
              example: 54321
            wage_declaration:
              type: number
              example: 50000.00
      404:
        description: Customer not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(customer_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for customer_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        cursor.close()
        connection.close()

        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        return jsonify(customer), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a customer
@customer_blueprint.route('/customers/<customer_id>', methods=['PUT'])
@admin_required
def update_customer(customer_id):
    """
    Update a customer's details
    ---
    tags:
      - Customers
    parameters:
      - name: customer_id
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
            first_name:
              type: string
              example: jale
            last_name:
              type: string
              example: korkmaz
            date_of_birth:
              type: string
              format: date
              example: 1985-05-15
            phone_number:
              type: string
              example: 9876543210
            email:
              type: string
              example: jale@example.com
            address_line1:
              type: string
              example: sehitler cd
            address_line2:
              type: string
              example: no 2
            city:
              type: string
              example: izmir
            zip_code:
              type: string
              example: 67890
            wage_declaration:
              type: number
              example: 60000.00
    responses:
      200:
        description: Customer updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Customer updated successfully
      400:
        description: Validation error
      404:
        description: Customer not found
      500:
        description: Internal server error
    """

    data = request.get_json()
    try:
        try:
            uuid.UUID(customer_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for customer_id'})

        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare update statements
        updates = []
        params = []
        if 'first_name' in data:
            updates.append("first_name = %s")
            params.append(data['first_name'])
        if 'last_name' in data:
            updates.append("last_name = %s")
            params.append(data['last_name'])
        if 'date_of_birth' in data:
            updates.append("date_of_birth = %s")
            params.append(data['date_of_birth'])
        if 'phone_number' in data:
            updates.append("phone_number = %s")
            params.append(data['phone_number'])
        if 'email' in data:
            updates.append("email = %s")
            params.append(data['email'])
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
        if 'wage_declaration' in data:
            updates.append("wage_declaration = %s")
            params.append(data['wage_declaration'])

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        # Add customer_id to the end of the params list
        params.append(customer_id)

        # Construct the SQL UPDATE query
        query = f"UPDATE customer SET {', '.join(updates)} WHERE customer_id = %s"

        # Execute the query and commit changes
        cursor.execute(query, tuple(params))
        connection.commit()

        # Check if any rows were affected
        if cursor.rowcount == 0:
            return jsonify({"error": "Customer not found"}), 404

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Customer updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a customer
@customer_blueprint.route('/customers/<customer_id>', methods=['DELETE'])
@admin_required
def delete_customer(customer_id):
    """
    Delete a customer
    ---
    tags:
      - Customers
    parameters:
      - name: customer_id
        in: path
        required: true
        type: string
        example: 123e4567-e89b-12d3-a456-426614174000
    responses:
      200:
        description: Customer deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Customer deleted successfully
      404:
        description: Customer not found
      500:
        description: Internal server error
    """

    try:
        try:
            uuid.UUID(customer_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for customer_id'})

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM customer WHERE customer_id = %s", (customer_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Customer not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Customer deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500