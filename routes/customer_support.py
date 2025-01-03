from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import uuid
from datetime import datetime
from database import get_db_connection
from .admin import admin_required

customer_support_blueprint = Blueprint('customer_support', __name__)

# Create a new support ticket
@customer_support_blueprint.route('/tickets', methods=['POST'])
@admin_required
def create_ticket():
    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['customer_id', 'employee_id', 'issue_description']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        # Get current date and time
        created_date = datetime.now()

        # Generate unique ticket ID
        ticket_id = str(uuid.uuid4())

        # Connect to database and create cursor
        connection = get_db_connection()
        cursor = connection.cursor()

        # Prepare SQL query
        query = """
        INSERT INTO customer_support (ticket_id, customer_id, employee_id, issue_description, status, created_date, resolved_date)
        VALUES (%s, %s, %s, %s, 'OPEN', %s, NULL)
        """
        params = (
        ticket_id,
        data['customer_id'],
        data['employee_id'],
        data['issue_description'],
        created_date,
        )

        # Execute query and commit changes
        cursor.execute(query, params)
        connection.commit()

        # Close connection and cursor
        cursor.close()
        connection.close()

        return jsonify({"message": "Ticket created successfully", "ticket_id": ticket_id}), 201

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all support tickets
@customer_support_blueprint.route('/tickets', methods=['GET'])
@admin_required
def get_tickets():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM customer_support")
        tickets = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify(tickets), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific support ticket by ID
@customer_support_blueprint.route('/tickets/<ticket_id>', methods=['GET'])
@admin_required
def get_ticket(ticket_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM customer_support WHERE ticket_id = %s", (ticket_id,))
        ticket = cursor.fetchone()
        cursor.close()
        connection.close()

        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404

        return jsonify(ticket), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update ticket status (e.g., 'IN_PROGRESS', 'RESOLVED')
@customer_support_blueprint.route('/tickets/<ticket_id>/status', methods=['PUT'])
@admin_required
def update_ticket_status(ticket_id):
    data = request.get_json()
    try:
        if 'status' not in data:
            return jsonify({"error": "Status is required"}), 400

        valid_statuses = ['OPEN', 'IN_PROGRESS', 'RESOLVED']
        if data['status'] not in valid_statuses:
            return jsonify({"error": "Invalid status. Valid statuses are: {', '.join(valid_statuses)}"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        # Set resolved_date if status is 'RESOLVED'
        if data['status'] == 'RESOLVED':
            resolved_date = datetime.now()
        else:
            resolved_date = None

        cursor.execute("""
        UPDATE customer_support 
        SET status = %s, resolved_date = %s 
        WHERE ticket_id = %s
        """, (data['status'], resolved_date, ticket_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Ticket not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Ticket status updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a ticket (Note: Ticket deletion might have business implications, handle with care)
@customer_support_blueprint.route('/tickets/<ticket_id>', methods=['DELETE'])
@admin_required
def delete_ticket(ticket_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM customer_support WHERE ticket_id = %s", (ticket_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Ticket not found"}), 404

        cursor.close()
        connection.close()

        return jsonify({"message": "Ticket deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500