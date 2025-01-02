from flask import Flask
from routes import routes_blueprint
from database import init_db
from flask_jwt_extended import JWTManager

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'super_secret_key'

jwt = JWTManager(app)

# Initialize the database
init_db()

# Register blueprints
app.register_blueprint(routes_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
