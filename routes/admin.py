from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from functools import wraps

admin_blueprint = Blueprint('admin', __name__)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        
        if claims.get('role', None) == "ADMIN":
            return fn(*args, **kwargs)
        
        return jsonify({"msg": "Admins only! Access forbidden."}), 403
    
    return wrapper

@admin_blueprint.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    """
    Admin Dashboard
    ---
    tags:
      - Admin
    responses:
      200:
        description: Welcome message for the admin dashboard
        schema:
          type: object
          properties:
            message:
              type: string
              example: Welcome to the admin dashboard!
      403:
        description: Admin access required
        schema:
          type: object
          properties:
            msg:
              type: string
              example: Admins only! Access forbidden.
    """

    return jsonify({"message": "Welcome to the admin dashboard!"}), 200
