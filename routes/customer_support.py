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

        try:
            uuid.UUID(data['customer_id'])
            uuid.UUID(data['employee_id'])
        except ValueError:
            return jsonify({'error': 'Invalid UUID for customer_id or employee_id'})

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
        try:
            uuid.UUID(ticket_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for ticket_id'})

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
        try:
            uuid.UUID(ticket_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for ticket_id'})

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
        try:
            uuid.UUID(ticket_id)
        except ValueError:
            return jsonify({'error': 'Invalid UUID string for ticket_id'})

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
    
@customer_support_blueprint.route('/top_resolvers', methods=['GET'])
@admin_required
def api_employees_top_resolvers():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        WITH ResolvedTickets AS (
            SELECT E.employee_id, E.first_name, E.last_name, COUNT(CS.ticket_id) AS resolved_tickets
            FROM employee E
            JOIN customer_support CS ON E.employee_id = CS.employee_id
            WHERE CS.status = 'RESOLVED'
            GROUP BY E.employee_id, E.first_name, E.last_name
        )
        SELECT employee_id, first_name, last_name, resolved_tickets
        FROM ResolvedTickets
        WHERE resolved_tickets = (
            SELECT MAX(resolved_tickets) FROM ResolvedTickets
        );
        """
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            return jsonify({'message': 'No employees found meeting the criteria.'}), 404

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching top resolvers.', 'details': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
