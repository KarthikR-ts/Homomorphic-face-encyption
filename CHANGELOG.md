# Changelog - Homomorphic Face Encryption

## [v0.3.0] - 2025-12-26 (Current)

### Real Biometric Processing
- **`face_service.py`** - Centralized face processing with OpenCV + FaceNet
- **`routes.py`** - Complete rewrite with real embedding extraction and comparison
- **`ConsentDashboard.jsx`** - Fixed API field mappings for consents and audit logs
- Removed TensorFlow dependency (switched to OpenCV Haar Cascade)

| Metric | Before | After |
|--------|--------|-------|
| Confidence | 0.95 (hardcoded) | Dynamic (real) |
| Face matching | Always true | Distance-based |

---

## [v0.2.0-beta] - 2025-12-25

### Consent Management
- 3-step consent onboarding wizard
- Privacy center with Active Consents, Auth History, and Data Management tabs
- GDPR/DPDP compliant export and deletion features
- Webcam integration with face overlay guide

---

## [v0.1.0] - 2025-12-24

### Initial Release
- Fixed OpenFHE imports with graceful fallback (MOCK MODE)
- Added CORS support for frontend communication
- Optimized Docker builds (reduced from 22GB+ to manageable size)
- Created React frontend with glassmorphism UI

---

## Tech Stack

- **Backend**: Python 3.11, Flask, SQLAlchemy, PostgreSQL, Redis
- **Frontend**: React 18, Vite
- **ML**: FaceNet, OpenCV Haar Cascade
- **Crypto**: CKKS (OpenFHE), AES-256 (pgcrypto)

## API Reference

| Endpoint | Purpose |
|----------|---------|
| `POST /api/auth/token` | Get JWT token |
| `POST /api/consent/grant` | Grant consent |
| `POST /api/register` | Enroll face |
| `POST /api/verify` | Verify identity |
| `POST /api/consent/export-data` | Export data (GDPR) |
| `POST /api/consent/delete-biometric-data` | Delete all data |
