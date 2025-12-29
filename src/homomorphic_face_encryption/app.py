"""Main Flask application for the privacy-preserving facial recognition system."""

from flask import Flask
from flask_jwt_extended import JWTManager
import os

from .api.routes import api_bp
from .database.models import create_tables

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'jwt-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'face_db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    jwt = JWTManager(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create database tables
    with app.app_context():
        create_tables()

    @app.route('/')
    def index():
        return {"message": "Privacy-Preserving Facial Recognition API"}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
