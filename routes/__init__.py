from flask import Blueprint

# Import all blueprints
from routes.user import user_blueprint
from routes.admin import admin_blueprint
from routes.account import account_blueprint
from routes.card import card_blueprint
from routes.branch import branch_blueprint
from routes.credit_score import credit_score_blueprint
from routes.customer import customer_blueprint
from routes.customer_support import customer_support_blueprint
from routes.employee import employee_blueprint
from routes.loan import loan_blueprint
from routes.loan_payment import loan_payment_blueprint
from routes.transaction import transaction_blueprint
from routes.auth import auth_blueprint

# Create a global blueprint to register all sub-blueprints
routes_blueprint = Blueprint('routes', __name__)

# Register sub-blueprints
routes_blueprint.register_blueprint(account_blueprint, url_prefix='/account')
routes_blueprint.register_blueprint(branch_blueprint, url_prefix='/branch')
routes_blueprint.register_blueprint(card_blueprint, url_prefix='/card')
routes_blueprint.register_blueprint(credit_score_blueprint, url_prefix='/credit_score')
routes_blueprint.register_blueprint(customer_blueprint, url_prefix='/customer')
routes_blueprint.register_blueprint(employee_blueprint, url_prefix='/employee')
routes_blueprint.register_blueprint(loan_payment_blueprint, url_prefix='/loan_payment')
routes_blueprint.register_blueprint(loan_blueprint, url_prefix='/loan')
routes_blueprint.register_blueprint(transaction_blueprint, url_prefix='/transaction')
routes_blueprint.register_blueprint(user_blueprint, url_prefix='/user')
routes_blueprint.register_blueprint(auth_blueprint, url_prefix='/auth')
routes_blueprint.register_blueprint(admin_blueprint, url_prefix='/admin')
routes_blueprint.register_blueprint(customer_support_blueprint, url_prefix='/customer_support')
