"""Consent management for GDPR compliance."""

from datetime import datetime
from ..database.models import ConsentLog, db


class ConsentManager:
    """Manages user consent for data processing operations."""

    def __init__(self):
        pass

    def set_consent(self, user_id: str, consent_given: bool):
        """Set consent status for a user."""
        action = "granted" if consent_given else "revoked"

        # Log the consent change
        log_entry = ConsentLog(user_id=user_id, action=action)
        db.add(log_entry)

        # Update user consent status
        user = db.query(db.User).filter_by(user_id=user_id).first()
        if user:
            user.consent_given = consent_given

        db.commit()

    def get_consent_status(self, user_id: str) -> bool:
        """Get current consent status for a user."""
        user = db.query(db.User).filter_by(user_id=user_id).first()
        return user.consent_given if user else False

    def get_consent_history(self, user_id: str) -> list:
        """Get consent change history for a user."""
        logs = db.query(ConsentLog).filter_by(user_id=user_id).order_by(ConsentLog.timestamp.desc()).all()
        return [
            {
                "action": log.action,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]

    def revoke_consent_and_delete_data(self, user_id: str):
        """Revoke consent and delete user's data (GDPR right to erasure)."""
        # Set consent to false
        self.set_consent(user_id, False)

        # Delete user data
        user = db.query(db.User).filter_by(user_id=user_id).first()
        if user:
            db.delete(user)
            db.commit()

        return {"message": f"Data for user {user_id} has been deleted"}
