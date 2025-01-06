from flask import Flask
from routes import routes_blueprint
from database import init_db
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from datetime import timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = 'super_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

jwt = JWTManager(app)

Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "Banking API",
        "description": "API documentation for the Banking System",
        "version": "1.0.0"
    },
    "host": "127.0.0.1:5000",
    "basePath": "/",
    "schemes": ["http"],
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer <your_token>'"
        }
    },
    "security": [{"BearerAuth": []}],
})

# Initialize the database
init_db()

# Register blueprints
app.register_blueprint(routes_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
