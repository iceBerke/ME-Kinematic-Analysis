# Simple blob detector for both dark and bright blobs in the original 2048x2048 images in the shortened directories (raw subfolder)
# Adjustable parameters: min and max area of the blobs
# This script only works for one image at a time, since its purpose is to optimize the parameters of blob detection for a specific experiment

# Script developed with the help of AI (Claude.AI)
# Last updated: 19/09/2025

# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import os

def detect_and_display_blobs(image_path,
                                                     min_distance=10,
                                                     clipLimit=0.6,
                                                     tileGridSize=(16, 16),
                                                     dark_minThreshold=0,
                                                     dark_maxThreshold=125,
                                                     dark_minArea=25,
                                                     dark_maxArea=800,
                                                     bright_minThreshold=85,
                                                     bright_maxThreshold=255,
                                                     bright_minArea=25,
                             bright_maxArea=800):
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None

    # Load image in grayscale
    img = cv.imread(image_path, 0)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return None

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) - same as original
    clahe = cv.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
    img_resized = cv.resize(img, (2048, 2048), interpolation=cv.INTER_LINEAR)
    img_clahe = clahe.apply(img_resized)

    # Setup blob detector parameters for DARK blobs (same as original)
    params_dark = cv.SimpleBlobDetector_Params()
    params_dark.minThreshold = dark_minThreshold
    params_dark.maxThreshold = dark_maxThreshold
    params_dark.filterByArea = True
    params_dark.minArea = dark_minArea
    params_dark.maxArea = dark_maxArea
    params_dark.filterByCircularity = False
    params_dark.filterByConvexity = False
    params_dark.filterByInertia = False

    # Setup blob detector parameters for BRIGHT blobs (same as original)
    params_bright = cv.SimpleBlobDetector_Params()
    params_bright.minThreshold = bright_minThreshold
    params_bright.maxThreshold = bright_maxThreshold
    params_bright.filterByArea = True
    params_bright.minArea = bright_minArea
    params_bright.maxArea = bright_maxArea
    params_bright.filterByCircularity = False
    params_bright.filterByConvexity = False
    params_bright.filterByInertia = False

    # Create detectors
    detector_dark = cv.SimpleBlobDetector_create(params_dark)
    detector_bright = cv.SimpleBlobDetector_create(params_bright)

    # Detect dark blobs on CLAHE image
    keypoints_dark = detector_dark.detect(img_clahe)

    # Detect bright blobs on inverted CLAHE image (same as original)
    img_inverted = cv.bitwise_not(img_clahe)
    keypoints_bright = detector_bright.detect(img_inverted)

    # Combine all keypoints
    keypoints = keypoints_dark + keypoints_bright

    # Filter keypoints by minimum distance (same as original)
    filtered_keypoints = []
    for kp in keypoints:
        if all(np.linalg.norm(np.array(kp.pt) - np.array(k.pt)) >= min_distance for k in filtered_keypoints):
            filtered_keypoints.append(kp)

    # Convert to color image for display
    img_display = cv.cvtColor(img_clahe, cv.COLOR_GRAY2RGB)

    # Draw orange hollow circles around detected blobs
    for kp in filtered_keypoints:
        center = (int(kp.pt[0]), int(kp.pt[1]))
        radius = int(kp.size / 2)

        # Draw orange hollow circle (outer and inner circles for hollow effect)
        cv.circle(img_display, center, radius + 2, (255, 165, 0), 2)  # Orange outer circle
        cv.circle(img_display, center, radius, (255, 140, 0), 1)  # Slightly darker orange inner circle

    # Count blobs by type
    dark_count = len(keypoints_dark)
    bright_count = len(keypoints_bright)
    total_blobs = len(filtered_keypoints)

    print(f"Detected blobs in {os.path.basename(image_path)}:")
    print(f"  Dark blobs: {dark_count}")
    print(f"  Bright blobs: {bright_count}")
    print(f"  Total filtered blobs: {total_blobs}")

    # Display the image using matplotlib
    plt.figure(figsize=(12, 12))
    plt.imshow(img_display)
    plt.title(f'Blob Detection: {os.path.basename(image_path)}\n'
              f'Dark: {dark_count}, Bright: {bright_count}, Total: {total_blobs}')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

    return {
        'keypoints_dark': keypoints_dark,
        'keypoints_bright': keypoints_bright,
        'filtered_keypoints': filtered_keypoints,
        'dark_count': dark_count,
        'bright_count': bright_count,
        'total_count': total_blobs
    }


# Hard-coded single image processing
if __name__ == "__main__":
    # HARD-CODED IMAGE PATH - Modify this to match your actual image file location
    image_path = "/media/general-max-riekeles/MMT_3/ME/ME_part2/Data/Nickel_4/shortened_5seconds/ecoli_control_24h_sample1_rec1.tif_files_changed/raw/ecoli_control_24h_sample1_rec1_00000.tif"

    # Process and display the single image
    if os.path.exists(image_path):
        print(f"Processing image: {image_path}")
        detect_and_display_blobs(image_path)
    else:
        print(f"Error: Image not found at {image_path}")
        print("Please update the 'image_path' variable with the correct path to your image file.")