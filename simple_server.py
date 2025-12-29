"""
Simple test server to check if the basic application components work.
This avoids the database initialization issue on Windows.
"""

import os
import logging
from flask import Flask

# Temporarily override database URL to avoid import issues
os.environ['DB_HOST'] = 'sqlite'
os.environ['DB_NAME'] = ':memory:'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

@app.route('/')
def hello():
    return {
        "service": "Homomorphic Face Encryption API",
        "status": "running",
        "message": "Basic server is working. Database initialization required for full functionality."
    }

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    logger.info("Starting simple test server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)