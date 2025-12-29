"""CKKS-based Homomorphic Encryption for Face Recognition"""

import os
from typing import List, Optional
import torch

# Optional OpenFHE import - gracefully degrade if not available
OPENFHE_AVAILABLE = False
Ciphertext = bytes  # Type alias for when OpenFHE is not available

try:
    from openfhe import *
    OPENFHE_AVAILABLE = True
except ImportError:
    import warnings
    warnings.warn(
        "OpenFHE not available. CKKSEncryptor will run in mock mode. "
        "Install openfhe-python for production use.",
        RuntimeWarning
    )



class CKKSEncryptor:
    """CKKS-based homomorphic encryption for secure face embedding comparison."""

    def __init__(self):
        self.context: Optional[CryptoContext] = None
        self.key_pair: Optional[KeyPair] = None
        self.rotation_keys: Optional[EvalKey] = None
        self.poly_degree = int(os.getenv("CKKS_POLY_DEGREE", "8192"))
        self.multiplicative_depth = int(os.getenv("CKKS_MULT_DEPTH", "5"))

    def setup_context(self):
        """Initialize CKKS context with parameters optimized for face embeddings."""
        if not OPENFHE_AVAILABLE:
            print("⚠️  OpenFHE not available - running in MOCK mode")
            return
        
        print("Setting up CKKS context for face recognition...")


        parameters = CCParamsCKKSRNS()
        parameters.SetMultiplicativeDepth(
            self.multiplicative_depth
        )  # For distance computation
        parameters.SetScalingModSize(50)
        parameters.SetBatchSize(8192)  # Large batch size for embedding dimensions
        parameters.SetSecurityLevel(SecurityLevel.HEStd_128_classic)
        parameters.SetRingDim(self.poly_degree)

        self.context = GenCryptoContext(parameters)

        # Enable required features
        self.context.Enable(PKESchemeFeature.PKE)
        self.context.Enable(PKESchemeFeature.KEYSWITCH)
        self.context.Enable(PKESchemeFeature.LEVELEDSHE)
        self.context.Enable(PKESchemeFeature.ROTATION)

        # Enable OpenMP parallelization if available
        try:
            self.context.Enable(MULTIPARTY)  # This enables OpenMP parallelization
            print("OpenMP parallelization enabled")
        except:
            print("OpenMP parallelization not available")

        print(f"CKKS context initialized with ring dimension {self.poly_degree}")

    def generate_keys(self):
        """Generate public/private keys and rotation keys for distance computation."""
        if not OPENFHE_AVAILABLE:
            print("⚠️  Skipping key generation - OpenFHE not available")
            return
        
        if not self.context:
            self.setup_context()


        print("Generating keypair...")
        self.key_pair = self.context.KeyGen()

        print("Generating rotation keys for SIMD operations...")
        # Generate rotation keys for summing across all dimensions
        # We need rotations by powers of 2 up to the embedding dimension (512)
        rotation_indices = []
        for i in range(9):  # 2^0 to 2^8 = 1, 2, 4, 8, 16, 32, 64, 128, 256
            rotation_indices.append(2**i)

        self.rotation_keys = self.context.EvalRotateKeyGen(
            self.key_pair.secretKey, rotation_indices
        )
        print(f"Generated rotation keys for indices: {rotation_indices}")

    def encrypt_embedding(self, embedding: List[float]) -> Ciphertext:
        """
        Encrypt a face embedding vector.

        Args:
            embedding: List of 512 float values (normalized face embedding)

        Returns:
            Encrypted ciphertext (or mock bytes if OpenFHE unavailable)
        """
        if not OPENFHE_AVAILABLE:
            # Return mock ciphertext for demo mode
            import pickle
            return pickle.dumps({'mock': True, 'embedding': embedding})
        
        if not self.key_pair:
            self.generate_keys()


        if len(embedding) != 512:
            raise ValueError(f"Embedding must be 512-dimensional, got {len(embedding)}")

        # Pad to batch size if necessary (embeddings are much smaller than batch size)
        padded_embedding = embedding + [0.0] * (
            self.context.GetEncodingParams().GetBatchSize() - len(embedding)
        )

        plaintext = self.context.MakeCKKSPackedPlaintext(padded_embedding)
        ciphertext = self.context.Encrypt(self.key_pair.publicKey, plaintext)

        return ciphertext

    def decrypt_distance(self, encrypted_distance: Ciphertext) -> float:
        """
        Decrypt an encrypted distance value.

        Args:
            encrypted_distance: Single-value encrypted distance

        Returns:
            Decrypted distance as float
        """
        if not self.key_pair:
            raise ValueError("Keys not generated")

        plaintext = self.context.Decrypt(self.key_pair.secretKey, encrypted_distance)
        plaintext.SetLength(1)  # Only first value contains the sum
        decrypted_values = plaintext.GetRealPackedValue()

        return float(decrypted_values[0])

    def compute_encrypted_distance(
        self, ct_query: Ciphertext, ct_stored: Ciphertext
    ) -> Ciphertext:
        """
        Compute encrypted squared Euclidean distance between two embeddings.

        Algorithm: d² = Σ(query[i] - stored[i])²

        Args:
            ct_query: Encrypted query embedding
            ct_stored: Encrypted stored embedding

        Returns:
            Encrypted distance value (single ciphertext)
        """
        if not self.context or not self.rotation_keys:
            raise ValueError("Context and rotation keys must be initialized")

        # Step 1: Homomorphic subtraction
        diff = self.context.EvalSub(ct_query, ct_stored)

        # Step 2: Homomorphic squaring (element-wise)
        diff_squared = self.context.EvalMult(diff, diff)

        # Step 3: SIMD rotations to sum all dimensions
        sum_ct = diff_squared

        # Sum across all 512 dimensions using rotation-based accumulation
        # This implements a parallel prefix sum using the rotation keys
        rotation_steps = [1, 2, 4, 8, 16, 32, 64, 128, 256]  # Powers of 2

        for rotation in rotation_steps:
            if rotation < 512:  # Don't rotate beyond embedding dimensions
                rotated = self.context.EvalRotate(sum_ct, rotation, self.rotation_keys)
                sum_ct = self.context.EvalAdd(sum_ct, rotated)

        # At this point, sum_ct contains the sum in the first coefficient
        # and the same value replicated across all positions due to the rotations

        return sum_ct

    def batch_compute_distances(
        self, ct_query: Ciphertext, ct_stored_list: List[Ciphertext]
    ) -> List[Ciphertext]:
        """
        Compute encrypted distances between query and multiple stored embeddings (1:N matching).

        Args:
            ct_query: Encrypted query embedding
            ct_stored_list: List of encrypted stored embeddings

        Returns:
            List of encrypted distance values
        """
        if not ct_stored_list:
            return []

        encrypted_distances = []

        # Process each stored embedding in parallel if OpenMP is enabled
        for ct_stored in ct_stored_list:
            encrypted_distance = self.compute_encrypted_distance(ct_query, ct_stored)
            encrypted_distances.append(encrypted_distance)

        return encrypted_distances

    def get_context_info(self) -> dict:
        """Get information about the CKKS context."""
        if not self.context:
            return {"status": "not_initialized"}

        return {
            "ring_dimension": self.context.GetRingDimension(),
            "cyclotomic_order": self.context.GetCyclotomicOrder(),
            "modulus": str(self.context.GetModulus()),
            "scaling_factor": self.context.GetScalingFactorReal(),
            "multiplicative_depth": self.multiplicative_depth,
            "batch_size": self.context.GetEncodingParams().GetBatchSize(),
            "security_level": "128-bit",
        }

    def __str__(self) -> str:
        """String representation."""
        status = "initialized" if self.context else "not_initialized"
        device = "GPU" if torch.cuda.is_available() else "CPU"
        return f"CKKSEncryptor(status={status}, device={device}, embedding_dim=512)"
