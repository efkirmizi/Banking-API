from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

admin_blueprint = Blueprint('admin', __name__)

def admin_required(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        if not current_user or current_user.get("role") != "ADMIN":
            return jsonify({"error": "Admin access required"}), 403
        return func(*args, **kwargs)
    return wrapper

@admin_blueprint.route('/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    return jsonify({"message": "Welcome to the admin dashboard!"}), 200
