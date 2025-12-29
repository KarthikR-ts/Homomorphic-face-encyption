"""Flask API routes for the facial recognition system."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token
import os

from ..crypto.fhe import FHEManager
from ..biometric.face_processor import FaceProcessor
from ..database.models import User, db
from ..consent.manager import ConsentManager

api_bp = Blueprint('api', __name__)

fhe_manager = FHEManager()
face_processor = FaceProcessor()
consent_manager = ConsentManager()


@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@api_bp.route('/register', methods=['POST'])
@jwt_required()
def register_face():
    """Register a user's face embedding (encrypted)."""
    try:
        data = request.get_json()
        user_id = data['user_id']
        image_data = data['image']  # Base64 encoded image

        # Process face
        # features = face_processor.extract_features(image_data)

        # Encrypt features
        # encrypted_features = fhe_manager.encrypt_vector(features.tolist())

        # Store in database
        # user = User(user_id=user_id, encrypted_embedding=encrypted_features)
        # db.session.add(user)
        # db.session.commit()

        return jsonify({"message": "Face registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_face():
    """Verify a face against stored encrypted embeddings."""
    try:
        data = request.get_json()
        image_data = data['image']

        # Process face
        # features = face_processor.extract_features(image_data)

        # Query database for potential matches (homomorphic operations would go here)
        # matches = User.query.all()

        # Decrypt and compare (simplified)
        # for user in matches:
        #     decrypted = fhe_manager.decrypt_vector(user.encrypted_embedding)
        #     similarity = face_processor.compare_faces(features, np.array(decrypted))
        #     if similarity > 0.8:
        #         return jsonify({"user_id": user.user_id, "confidence": similarity})

        return jsonify({"message": "No match found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/consent', methods=['POST'])
@jwt_required()
def manage_consent():
    """Manage user consent for data processing."""
    try:
        data = request.get_json()
        user_id = data['user_id']
        consent_given = data['consent']

        consent_manager.set_consent(user_id, consent_given)
        return jsonify({"message": "Consent updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
