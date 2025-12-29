# Homomorphic Face Encryption

A privacy-preserving facial recognition system that uses Fully Homomorphic Encryption (FHE) to protect user biometric data while enabling secure face verification operations.

## Features

- **Privacy-Preserving**: Uses homomorphic encryption to perform computations on encrypted data without decryption
- **Facial Recognition**: Integrates FaceNet and MTCNN for robust face detection and feature extraction
- **GDPR Compliant**: Built-in consent management and data deletion capabilities
- **Modular Architecture**: Separated concerns with crypto, biometric, API, database, and consent modules
- **Containerized**: Docker Compose setup with Flask API, PostgreSQL, and Redis

## Project Structure

```
src/homomorphic_face_encryption/
├── crypto/          # FHE operations
├── biometric/       # Face processing and recognition
├── api/            # Flask REST API
├── database/       # PostgreSQL ORM models
└── consent/        # GDPR compliance management
```

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd homomorphic-face-encryption
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Environment setup**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

4. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/register` - Register face embedding (JWT required)
- `POST /api/verify` - Verify face against stored embeddings (JWT required)
- `POST /api/consent` - Manage user consent (JWT required)

## Development

- **Pre-commit hooks**: Automatically installed for code quality
- **Testing**: Run tests with `poetry run pytest`
- **Linting**: Code formatted with Black, linted with Flake8, type-checked with MyPy

## Dependencies

- Python 3.10+
- Poetry for dependency management
- Flask for API
- SQLAlchemy for ORM
- PostgreSQL with pgcrypto extension
- Redis for session management

## License

[License information]
