#!/usr/bin/env python3
"""
Simple Validation Test for FaceDetector
Basic test without heavy ML dependencies
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_face_detector_import():
    """Test if FaceDetector can be imported (without running detection)."""
    try:
        from homomorphic_face_encryption.biometric.face_detector import FaceDetector
        print("FaceDetector import successful")
        return True
    except ImportError as e:
        print(f"FaceDetector import failed: {e}")
        return False

def test_basic_structure():
    """Test if the basic file structure and classes exist."""
    detector_path = Path("src/homomorphic_face_encryption/biometric/face_detector.py")

    if not detector_path.exists():
        print(f"FaceDetector file not found: {detector_path}")
        return False

    # Read the file and check for key components
    with open(detector_path, 'r') as f:
        content = f.read()

    checks = [
        ("class FaceDetector:", "FaceDetector class definition"),
        ("def __init__(self):", "__init__ method"),
        ("def detect_and_align(self,", "detect_and_align method"),
        ("MTCNN(", "MTCNN initialization"),
        ("image_size=160", "Correct image_size parameter"),
        ("margin=20", "Correct margin parameter"),
        ("min_face_size=40", "Correct min_face_size parameter"),
        ("thresholds=[0.6, 0.7, 0.7]", "Correct thresholds parameter"),
        ("factor=0.709", "Correct factor parameter"),
    ]

    passed = 0
    for check, description in checks:
        if check in content:
            print(f"Found: {description}")
            passed += 1
        else:
            print(f"Missing: {description}")

    print(f"\nStructure check: {passed}/{len(checks)} components found")

    # Check if the method has the right signature
    if "def detect_and_align(self, image_path: str)" in content:
        print("detect_and_align method signature correct")
    else:
        print("detect_and_align method signature incorrect")

    return passed == len(checks)

def test_dependencies():
    """Test if required dependencies are available."""
    dependencies = ['cv2', 'PIL', 'torch', 'numpy']

    available = 0
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"{dep} available")
            available += 1
        except ImportError:
            print(f"{dep} not available")

    print(f"\nDependencies: {available}/{len(dependencies)} available")
    return available >= 2  # At least basic dependencies

def main():
    """Run all validation tests."""
    print("Simple FaceDetector Validation Test")
    print("=" * 50)

    tests = [
        ("File Structure", test_basic_structure),
        ("Dependencies", test_dependencies),
        ("Import Test", test_face_detector_import),
    ]

    results = []
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        result = test_func()
        results.append((name, result))

    print("\n" + "=" * 50)
    print("Test Results:")

    all_passed = True
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"   {name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\nAll basic validations passed!")
        print("Note: Full functionality test requires ML libraries (facenet-pytorch, mtcnn)")
        print("Run 'pip install facenet-pytorch mtcnn opencv-python torch torchvision' to enable full testing")
    else:
        print("\nSome validations failed. Check the output above.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
