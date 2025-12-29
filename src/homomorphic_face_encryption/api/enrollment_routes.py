"""
Enrollment API Routes

Flask Blueprint providing endpoints for biometric template enrollment:
- POST /api/enroll - Enroll a user's face embedding (encrypted) with client-side processing

This endpoint allows clients to perform face detection/processing locally and submit
encrypted embeddings directly, bypassing server-side image processing.

Rate Limiting: Max 5 enrollment attempts per user per hour to prevent brute-force attacks.
"""

import base64
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..database import (
    User,
    BiometricTemplate,
    AuditLog,
    ConsentPurpose,
    AuditAction,
    SessionLocal,
    encrypt_json_metadata,
    generate_encryption_params_hash,
)
from .consent_middleware import consent_required

logger = logging.getLogger(__name__)

enrollment_bp = Blueprint('enrollment', __name__)

def get_db():
    """Get database session for request."""
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db


def get_redis():
    """Get Redis client from app config."""
    from flask import current_app
    return current_app.config.get('REDIS_CLIENT')


def create_audit_log(
    user_id: UUID,
    action: AuditAction,
    success: bool,
    metadata: dict = None,
    error_message: str = None
) -> None:
    """Create audit log entry for biometric operation."""
    try:
        db = get_db()
        
        if metadata is None:
            metadata = {}
        
        # Add common fields
        if request:
            metadata["ip_address"] = request.remote_addr or "unknown"
            metadata["user_agent"] = request.headers.get('User-Agent', 'unknown')[:200]
            metadata["endpoint"] = request.endpoint
        
        log = AuditLog(
            user_id=user_id,
            action=action,
            metadata_encrypted=encrypt_json_metadata(metadata),
            success=success,
            error_message=error_message
        )
        
        db.add(log)
        db.commit()
        
    except Exception as e:
        logger.warning(f"Failed to create audit log: {e}")


def check_rate_limit(user_id: UUID, limit: int = 5, window_hours: int = 1) -> bool:
    """
    Check if user has exceeded enrollment rate limit.
    
    Args:
        user_id: User UUID
        limit: Max attempts allowed
        window_hours: Time window in hours
        
    Returns:
        bool: True if within limit, False if exceeded
    """
    redis_client = get_redis()
    if not redis_client:
        # If Redis is not available, allow the request (fallback behavior)
        return True
    
    key = f"enrollment_limit:{user_id}"
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=window_hours)
    
    try:
        # Use Redis sorted set to track attempts with timestamps
        # Remove attempts outside the window
        redis_client.zremrangebyscore(key, "-inf", window_start.timestamp())
        
        # Count current attempts in window
        current_attempts = redis_client.zcard(key)
        
        if current_attempts >= limit:
            return False
        
        # Add current attempt with timestamp
        redis_client.zadd(key, {f"attempt:{now.timestamp()}": now.timestamp()})
        
        # Set expiration for the key to clean up automatically
        redis_client.expire(key, int(timedelta(hours=window_hours).total_seconds()))
        
        return True
    except Exception as e:
        logger.warning(f"Rate limit check failed: {e}")
        # If rate limiting fails, allow the request (fail open for usability)
        return True


@enrollment_bp.route('/enroll', methods=['POST'])
@jwt_required()
@consent_required(ConsentPurpose.AUTHENTICATION)
def enroll_face():
    """
    Enroll a user's face embedding (encrypted).
    
    Requires AUTHENTICATION consent.
    
    Request Body:
        {
            "user_id": "uuid",  // Should match JWT identity
            "encrypted_embedding_base64": "str",  // Base64-encoded CKKS ciphertext
            "embedding_dimension": 512,  // 512 or 128
            "encryption_params": {  // CKKS parameters for verification
                "poly_degree": 8192,
                "scale_bits": 50,
                "mult_depth": 5
            },
            "liveness_score": 0.92  // From client-side liveness detection
        }
    
    Response:
        {
            "status": "enrolled",
            "template_id": "uuid",
            "enrolled_at": "timestamp"
        }
    
    Flow:
        1. Verify consent (handled by middleware)
        2. Validate encryption parameters match server config
        3. Validate liveness score > 0.85
        4. Check rate limit (max 5 per hour)
        5. Check user doesn't already have active template
        6. Decode base64 to binary ciphertext
        7. Store encrypted template
        8. Create audit log
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        # Get user ID from JWT and validate against request
        jwt_user_id_str = get_jwt_identity()
        jwt_user_id = UUID(jwt_user_id_str)
        
        # Validate user_id in request matches JWT identity
        request_user_id_str = data.get('user_id')
        if not request_user_id_str:
            return jsonify({"error": "user_id is required in request body"}), 400
        
        request_user_id = UUID(request_user_id_str)
        if jwt_user_id != request_user_id:
            return jsonify({"error": "user_id in request doesn't match JWT identity"}), 403
        
        # Validate required fields
        required_fields = [
            'encrypted_embedding_base64',
            'embedding_dimension',
            'encryption_params',
            'liveness_score'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate embedding dimension
        embedding_dimension = data.get('embedding_dimension')
        if embedding_dimension not in [128, 512]:
            return jsonify({"error": "embedding_dimension must be 128 or 512"}), 400
        
        # Validate encryption parameters
        encryption_params = data.get('encryption_params')
        if not isinstance(encryption_params, dict):
            return jsonify({"error": "encryption_params must be an object"}), 400
        
        required_params = ['poly_degree', 'scale_bits', 'mult_depth']
        for param in required_params:
            if param not in encryption_params:
                return jsonify({"error": f"encryption_params.{param} is required"}), 400
        
        # Verify encryption parameters match server configuration
        expected_poly_degree = int(request.environ.get('CKKS_POLY_DEGREE', 8192))
        expected_mult_depth = int(request.environ.get('CKKS_MULT_DEPTH', 5))
        expected_scale_bits = 50  # Default scale bits
        
        if (encryption_params['poly_degree'] != expected_poly_degree or
            encryption_params['mult_depth'] != expected_mult_depth or
            encryption_params.get('scale_bits', expected_scale_bits) != expected_scale_bits):
            return jsonify({
                "error": "encryption_params do not match server configuration",
                "expected": {
                    "poly_degree": expected_poly_degree,
                    "mult_depth": expected_mult_depth,
                    "scale_bits": expected_scale_bits
                }
            }), 400
        
        # Validate liveness score
        liveness_score = data.get('liveness_score')
        if not isinstance(liveness_score, (int, float)) or liveness_score < 0 or liveness_score > 1:
            return jsonify({"error": "liveness_score must be a float between 0 and 1"}), 400
        
        if liveness_score <= 0.85:
            return jsonify({"error": "liveness_score must be greater than 0.85 for genuine face"}), 400
        
        # Check rate limit
        if not check_rate_limit(jwt_user_id, limit=5, window_hours=1):
            create_audit_log(
                user_id=jwt_user_id,
                action=AuditAction.ENROLL,
                success=False,
                metadata={
                    "reason": "rate_limit_exceeded",
                    "liveness_score": liveness_score
                }
            )
            return jsonify({"error": "Rate limit exceeded: max 5 enrollment attempts per hour"}), 429
        
        # Get database session
        db = get_db()
        
        # Verify user exists
        user = db.query(User).filter_by(id=jwt_user_id, is_active=True).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check if user already has an active template (enforce 1 template per user policy)
        existing_template = db.query(BiometricTemplate).filter_by(
            user_id=jwt_user_id,
            is_active=True
        ).first()
        
        if existing_template:
            create_audit_log(
                user_id=jwt_user_id,
                action=AuditAction.ENROLL,
                success=False,
                metadata={
                    "reason": "template_already_exists",
                    "existing_template_id": str(existing_template.id),
                    "liveness_score": liveness_score
                }
            )
            return jsonify({
                "error": "User already has an active biometric template",
                "message": "Please delete existing template before enrolling a new one, or use re-enrollment flow"
            }), 409
        
        # Decode base64 to binary ciphertext
        encrypted_embedding_b64 = data.get('encrypted_embedding_base64')
        try:
            encrypted_embedding_binary = base64.b64decode(encrypted_embedding_b64)
        except Exception as e:
            logger.warning(f"Base64 decode error for user {jwt_user_id}: {e}")
            create_audit_log(
                user_id=jwt_user_id,
                action=AuditAction.ENROLL,
                success=False,
                metadata={
                    "reason": "invalid_base64_encoding",
                    "liveness_score": liveness_score
                },
                error_message=str(e)
            )
            return jsonify({"error": "Invalid base64 encoding for encrypted embedding"}), 400
        
        # Compute SHA256 hash of current CKKS params for encryption_params_hash
        params_hash = generate_encryption_params_hash(
            poly_degree=encryption_params['poly_degree'],
            mult_depth=encryption_params['mult_depth'],
            security_level="HEStd_128_classic"  # Default security level
        )
        
        # Create biometric template
        template = BiometricTemplate(
            user_id=jwt_user_id,
            encrypted_embedding=encrypted_embedding_binary,
            embedding_dimension=embedding_dimension,
            encryption_params_hash=params_hash,
            is_active=True
        )
        
        db.add(template)
        db.commit()
        
        # Create audit log
        enrolled_at = datetime.now(timezone.utc)
        create_audit_log(
            user_id=jwt_user_id,
            action=AuditAction.ENROLL,
            success=True,
            metadata={
                "template_id": str(template.id),
                "template_size": len(encrypted_embedding_binary),
                "embedding_dimension": embedding_dimension,
                "params_hash": params_hash,
                "liveness_score": liveness_score
            }
        )
        
        # Update user's last authentication time
        user.last_authentication = enrolled_at
        db.commit()
        
        return jsonify({
            "status": "enrolled",
            "template_id": str(template.id),
            "enrolled_at": enrolled_at.isoformat()
        }), 201
        
    except ValueError as e:
        # Handle UUID parsing errors
        logger.warning(f"Invalid UUID in enroll request: {e}")
        return jsonify({"error": "Invalid user_id format"}), 400
    except Exception as e:
        logger.exception("Face enrollment error")
        jwt_user_id = None
        try:
            jwt_user_id = UUID(get_jwt_identity())
        except:
            pass
        
        if jwt_user_id:
            create_audit_log(
                user_id=jwt_user_id,
                action=AuditAction.ENROLL,
                success=False,
                error_message=str(e)
            )
        
        return jsonify({"error": "Enrollment failed"}), 500