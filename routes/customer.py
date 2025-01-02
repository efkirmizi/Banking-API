from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from database import get_db_connection
from admin import admin_required

customer_blueprint = Blueprint('customer', __name__)

# create a new customer
@customer_blueprint.route('/customers', methods=['POST'])
@admin_required
def create_customer():
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
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
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
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
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
    data = request.get_json()
    try:
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
    try:
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