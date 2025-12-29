#!/usr/bin/env python3
"""
Real-time Camera Test for FaceDetector
Tests face detection and alignment using webcam feed
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, 'src')

def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        import torch
        from facenet_pytorch import MTCNN
        from PIL import Image
        print("All ML dependencies available - full functionality enabled")
        return True
    except ImportError as e:
        print(f"ML dependencies not available: {e}")
        print("Running in demo mode with mock face detection")
        return False

def create_mock_face_detector():
    """Create a mock face detector for demo purposes."""
    class MockFaceDetector:
        def __init__(self):
            self.frame_count = 0

        def detect_and_align(self, image_path):
            """Mock detection that returns synthetic results."""
            # Create a mock face tensor (160x160x3)
            mock_face = np.random.rand(160, 160, 3).astype(np.float32)
            mock_face = (mock_face - 0.5) / 0.5  # Normalize to [-1, 1]
            mock_tensor = torch.from_numpy(mock_face).permute(2, 0, 1).float()

            # Mock metadata
            mock_metadata = {
                'bbox': [200, 150, 240, 190],  # [x1, y1, x2, y2]
                'confidence': 0.98,
                'landmarks': {
                    'left_eye': [220, 170],
                    'right_eye': [260, 170],
                    'nose': [240, 185],
                    'mouth_left': [225, 200],
                    'mouth_right': [255, 200]
                },
                'image_path': image_path,
                'face_index': 0
            }

            return mock_tensor, mock_metadata

    try:
        import torch
        return MockFaceDetector()
    except ImportError:
        print("Even torch not available - cannot create mock detector")
        return None

def initialize_face_detector():
    """Initialize FaceDetector with fallback to mock."""
    if check_dependencies():
        try:
            from homomorphic_face_encryption.biometric.face_detector import FaceDetector
            detector = FaceDetector()
            print("Real FaceDetector initialized")
            return detector, True
        except Exception as e:
            print(f"Failed to initialize real FaceDetector: {e}")
            print("Falling back to mock detector")
            return create_mock_face_detector(), False
    else:
        print("Using mock face detector for demonstration")
        return create_mock_face_detector(), False

def draw_detection_results(frame, detector_result, is_real_detector):
    """Draw detection results on the frame."""
    if detector_result is None:
        return frame

    face_tensor, metadata = detector_result

    # Draw bounding box
    bbox = metadata['bbox']
    cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])),
                  (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)

    # Draw confidence
    confidence = metadata['confidence']
    conf_text = f"Conf: {confidence:.2f}"
    cv2.putText(frame, conf_text, (int(bbox[0]), int(bbox[1]) - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Draw landmarks
    landmarks = metadata['landmarks']
    landmark_colors = {
        'left_eye': (255, 0, 0),
        'right_eye': (0, 255, 0),
        'nose': (0, 0, 255),
        'mouth_left': (255, 255, 0),
        'mouth_right': (255, 0, 255)
    }

    for name, point in landmarks.items():
        cv2.circle(frame, (int(point[0]), int(point[1])), 3,
                  landmark_colors.get(name, (255, 255, 255)), -1)
        cv2.putText(frame, name[:3], (int(point[0]) + 5, int(point[1]) - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, landmark_colors.get(name, (255, 255, 255)), 1)

    # Add mode indicator
    mode_text = "REAL DETECTOR" if is_real_detector else "MOCK DETECTOR"
    cv2.putText(frame, mode_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0) if is_real_detector else (0, 165, 255), 2)

    # Add instructions
    cv2.putText(frame, "Press 'Q' to quit, 'S' to save frame", (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return frame

def save_frame(frame, detector_result, frame_count):
    """Save current frame and detection results."""
    timestamp = int(time.time())
    filename = f"camera_capture_{timestamp}_{frame_count}.jpg"

    # Save frame
    cv2.imwrite(filename, frame)
    print(f"Frame saved: {filename}")

    # Save detection metadata if available
    if detector_result:
        face_tensor, metadata = detector_result
        metadata_file = f"camera_capture_{timestamp}_{frame_count}_metadata.txt"
        with open(metadata_file, 'w') as f:
            f.write(f"Confidence: {metadata['confidence']}\n")
            f.write(f"Bounding Box: {metadata['bbox']}\n")
            f.write(f"Landmarks: {metadata['landmarks']}\n")
        print(f"Metadata saved: {metadata_file}")

def main():
    """Run the camera test."""
    print("FaceDetector Camera Test")
    print("=" * 50)

    # Initialize detector
    detector, is_real_detector = initialize_face_detector()
    if detector is None:
        print("ERROR: Could not initialize any detector")
        return 1

    # Initialize camera
    print("Initializing camera...")
    cap = cv2.VideoCapture(0)  # Use default camera

    if not cap.isOpened():
        print("ERROR: Could not open camera")
        return 1

    print("Camera opened successfully")
    print("Controls:")
    print("  - Press 'Q' to quit")
    print("  - Press 'S' to save current frame")
    print("  - Press 'D' to toggle detection on/off")
    print()

    # Camera properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    print(f"Camera resolution: {frame_width}x{frame_height}")
    print(f"Camera FPS: {fps}")

    # Processing variables
    detection_enabled = True
    frame_count = 0
    last_detection_time = 0
    detection_interval = 0.1  # Process every 100ms

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to read frame")
                break

            frame_count += 1
            current_time = time.time()

            # Process detection at intervals
            detector_result = None
            if detection_enabled and (current_time - last_detection_time) > detection_interval:
                try:
                    # Save frame temporarily for detection
                    temp_image_path = f"temp_frame_{frame_count}.jpg"
                    cv2.imwrite(temp_image_path, frame)

                    # Run detection
                    detector_result = detector.detect_and_align(temp_image_path)
                    last_detection_time = current_time

                    # Clean up temp file
                    try:
                        os.remove(temp_image_path)
                    except:
                        pass

                except Exception as e:
                    print(f"Detection error: {e}")
                    detector_result = None

            # Draw results on frame
            display_frame = draw_detection_results(frame.copy(), detector_result, is_real_detector)

            # Add FPS counter
            fps_text = f"FPS: {1.0 / max(current_time - last_detection_time, 0.001):.1f}"
            cv2.putText(display_frame, fps_text, (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Show frame
            cv2.imshow('FaceDetector Camera Test', display_frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Exiting...")
                break
            elif key == ord('s'):
                save_frame(frame, detector_result, frame_count)
            elif key == ord('d'):
                detection_enabled = not detection_enabled
                status = "ENABLED" if detection_enabled else "DISABLED"
                print(f"Detection {status}")

    except KeyboardInterrupt:
        print("Interrupted by user")

    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

        # Clean up any remaining temp files
        for temp_file in Path(".").glob("temp_frame_*.jpg"):
            try:
                temp_file.unlink()
            except:
                pass

    print("Camera test completed")
    return 0

if __name__ == "__main__":
    exit(main())
