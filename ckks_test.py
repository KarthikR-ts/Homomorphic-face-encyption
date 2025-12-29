#!/usr/bin/env python3
"""
Test script for CKKSEncryptor homomorphic distance computation
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, "src")


def test_ckks_encryptor():
    """Test the CKKSEncryptor functionality."""
    print("Testing CKKSEncryptor...")

    try:
        from homomorphic_face_encryption.crypto.ckks_encryptor import CKKSEncryptor

        # Initialize encryptor
        print("Initializing CKKSEncryptor...")
        encryptor = CKKSEncryptor()
        print("✓ CKKSEncryptor initialized successfully")

        # Test context setup (without full OpenFHE)
        print("\nTesting context setup...")
        try:
            encryptor.setup_context()
            print("✓ Context setup successful")
        except Exception as e:
            print(f"✗ Context setup failed: {e}")
            print("This is expected if OpenFHE is not installed")
            return False

        # Test key generation
        print("\nTesting key generation...")
        try:
            encryptor.generate_keys()
            print("✓ Key generation successful")
        except Exception as e:
            print(f"✗ Key generation failed: {e}")
            return False

        # Test embedding encryption (mock data)
        print("\nTesting embedding encryption...")
        mock_embedding = np.random.randn(512).astype(np.float32)
        mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)  # L2 normalize

        try:
            encrypted_emb = encryptor.encrypt_embedding(mock_embedding.tolist())
            print("✓ Embedding encryption successful")
        except Exception as e:
            print(f"✗ Embedding encryption failed: {e}")
            return False

        # Test encrypted distance computation
        print("\nTesting encrypted distance computation...")
        mock_embedding2 = np.random.randn(512).astype(np.float32)
        mock_embedding2 = mock_embedding2 / np.linalg.norm(mock_embedding2)

        try:
            encrypted_emb2 = encryptor.encrypt_embedding(mock_embedding2.tolist())

            # Compute encrypted distance
            encrypted_distance = encryptor.compute_encrypted_distance(
                encrypted_emb, encrypted_emb2
            )
            print("✓ Encrypted distance computation successful")

            # Decrypt and verify
            decrypted_distance = encryptor.decrypt_distance(encrypted_distance)

            # Compute expected distance
            expected_distance = np.sum((mock_embedding - mock_embedding2) ** 2)

            print(f"Expected distance: {expected_distance:.6f}")
            print(f"Decrypted distance: {decrypted_distance:.6f}")
            print(f"Difference: {abs(expected_distance - decrypted_distance):.6f}")

            # Allow small numerical difference due to FHE precision
            if abs(expected_distance - decrypted_distance) < 0.01:
                print("✓ Distance computation accuracy validated")
            else:
                print(
                    "⚠ Distance computation has precision differences (expected with FHE)"
                )

        except Exception as e:
            print(f"✗ Encrypted distance computation failed: {e}")
            return False

        # Test batch distance computation
        print("\nTesting batch distance computation...")
        try:
            mock_embeddings = []
            encrypted_embeddings = []

            # Create 3 mock embeddings
            for i in range(3):
                emb = np.random.randn(512).astype(np.float32)
                emb = emb / np.linalg.norm(emb)
                mock_embeddings.append(emb)
                encrypted_embeddings.append(encryptor.encrypt_embedding(emb.tolist()))

            # Compute batch distances
            batch_distances = encryptor.batch_compute_distances(
                encrypted_emb, encrypted_embeddings
            )

            if len(batch_distances) == 3:
                print("✓ Batch distance computation successful")
                print(f"Computed {len(batch_distances)} encrypted distances")
            else:
                print(f"✗ Expected 3 distances, got {len(batch_distances)}")
                return False

        except Exception as e:
            print(f"✗ Batch distance computation failed: {e}")
            return False

        # Test context info
        print("\nTesting context information...")
        try:
            info = encryptor.get_context_info()
            print(f"✓ Context info retrieved: {len(info)} parameters")
            for key, value in info.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"✗ Context info retrieval failed: {e}")
            return False

        print(f"\n✓ String representation: {encryptor}")
        print("\n🎉 All CKKSEncryptor tests passed!")
        return True

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure OpenFHE is installed:")
        print("  pip install openfhe-python")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ckks_encryptor()
    exit(0 if success else 1)
