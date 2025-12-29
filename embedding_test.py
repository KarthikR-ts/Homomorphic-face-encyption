#!/usr/bin/env python3
"""
Test script for EmbeddingExtractor
"""

import sys
import os
import numpy as np
import torch

# Add src to path
sys.path.insert(0, 'src')

def test_embedding_extractor():
    """Test the EmbeddingExtractor functionality."""
    print("Testing EmbeddingExtractor...")

    try:
        from homomorphic_face_encryption.biometric.embedding_extractor import EmbeddingExtractor

        # Initialize extractor
        print("Initializing EmbeddingExtractor...")
        extractor = EmbeddingExtractor()
        print("✓ EmbeddingExtractor initialized successfully")

        # Test single embedding extraction
        print("\nTesting single embedding extraction...")

        # Create a mock aligned face tensor (normalized to [-1, 1])
        mock_face = torch.randn(3, 160, 160)  # Random face tensor
        mock_face = (mock_face - mock_face.min()) / (mock_face.max() - mock_face.min())  # Normalize to [0, 1]
        mock_face = (mock_face - 0.5) / 0.5  # Scale to [-1, 1]

        embedding = extractor.extract_embedding(mock_face)

        # Validate embedding properties
        assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
        assert embedding.dtype == np.float32, f"Embedding dtype should be float32, got {embedding.dtype}"
        assert embedding.shape == (512,), f"Embedding shape should be (512,), got {embedding.shape}"

        # Check L2 normalization (should be approximately 1.0)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5, f"Embedding should be L2 normalized, norm = {norm}"

        print(f"✓ Single embedding extracted: shape={embedding.shape}, dtype={embedding.dtype}, norm={norm:.6f}")

        # Test batch extraction
        print("\nTesting batch embedding extraction...")
        mock_faces = [mock_face, mock_face * 0.9, mock_face * 1.1]  # 3 variations
        embeddings = extractor.batch_extract(mock_faces)

        assert len(embeddings) == 3, f"Should return 3 embeddings, got {len(embeddings)}"
        for i, emb in enumerate(embeddings):
            assert emb.shape == (512,), f"Embedding {i} shape should be (512,), got {emb.shape}"
            norm = np.linalg.norm(emb)
            assert abs(norm - 1.0) < 1e-5, f"Embedding {i} should be normalized, norm = {norm}"
            print(f"✓ Batch embedding {i}: norm={norm:.6f}")

        # Test distance computation
        print("\nTesting distance computation...")
        dist_same = extractor.compute_distance(embedding, embedding)
        dist_different = extractor.compute_distance(embeddings[0], embeddings[1])

        assert abs(dist_same) < 1e-6, f"Distance between same embedding should be ~0, got {dist_same}"
        assert dist_different > 0, f"Distance between different embeddings should be >0, got {dist_different}"
        print(f"✓ Distance same: {dist_same:.6f}")
        print(f"✓ Distance different: {dist_different:.6f}")

        # Test similarity computation
        print("\nTesting similarity computation...")
        sim_same = extractor.compute_similarity(embedding, embedding)
        sim_different = extractor.compute_similarity(embeddings[0], embeddings[1])

        assert abs(sim_same - 1.0) < 1e-6, f"Similarity between same embedding should be ~1, got {sim_same}"
        assert sim_different < 1.0, f"Similarity between different embeddings should be <1, got {sim_different}"
        print(f"✓ Similarity same: {sim_same:.6f}")
        print(f"✓ Similarity different: {sim_different:.6f}")

        # Test utility methods
        print("\nTesting utility methods...")
        dims = extractor.get_embedding_dimensions()
        assert dims == 512, f"Embedding dimensions should be 512, got {dims}"
        print(f"✓ Embedding dimensions: {dims}")

        print(f"✓ String representation: {extractor}")

        print("\n🎉 All EmbeddingExtractor tests passed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure facenet_pytorch and torch are installed:")
        print("pip install facenet-pytorch torch torchvision")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_embedding_extractor()
    exit(0 if success else 1)
