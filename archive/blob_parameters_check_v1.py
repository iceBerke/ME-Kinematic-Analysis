# Simple blob detector for both dark and bright blobs in the original 2048x2048 images in the shortened directories (raw subfolder)
# Adjustable parameters: min and max area of the blobs
# This script only works for one image at a time, since its purpose is to optimize the parameters of blob detection for a specific experiment

# Script developed with the help of AI (Claude.AI)
# Last updated: 19/09/2025

# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

# Global parameters for blob detection
MIN_AREA = 50
MAX_AREA = 750


def detect_blobs(im, invert=True):
    if invert:
        im = cv.bitwise_not(im)
    params = cv.SimpleBlobDetector_Params()
    params.minThreshold = 0
    params.maxThreshold = 255
    params.filterByArea = True
    params.minArea = MIN_AREA
    params.maxArea = MAX_AREA
    params.filterByCircularity = False
    params.minCircularity = 0.1
    params.filterByConvexity = False
    params.minConvexity = 0.1
    params.filterByInertia = False
    params.minInertiaRatio = 0.1
    params.maxInertiaRatio = 1.0

    detector = cv.SimpleBlobDetector_create(params)
    return detector.detect(im)


def display_image_with_blobs(img, keypoints):
    # Draw detected blobs as red circles.
    img_with_keypoints = cv.drawKeypoints(img, keypoints, np.array([]), (0, 0, 255),
                                          cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    # Resize image to half the size
    height, width = img_with_keypoints.shape[:2]
    img_resized = cv.resize(img_with_keypoints, (width // 2, height // 2))

    # Display the image
    plt.imshow(cv.cvtColor(img_resized, cv.COLOR_BGR2RGB))
    plt.axis('off')  # Turn off axis
    plt.show()


def process_single_image(image_path):
    # Create a CLAHE object for contrast enhancement
    clahe = cv.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))

    # Load the image in grayscale
    img = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Failed to load image: {image_path}")
        return

    # Apply CLAHE to enhance contrast
    img_clahe = clahe.apply(img)

    # Detect blobs without inverting and with inverting
    key_points_original = detect_blobs(img_clahe, invert=False)
    key_points_inverted = detect_blobs(img_clahe, invert=True)

    # Combine keypoints from both detections
    all_key_points = key_points_original + key_points_inverted

    # Display the image with detected blobs
    display_image_with_blobs(img_clahe, all_key_points)
    print(MIN_AREA)
    print(MAX_AREA)
    print(f"Detection Parameters - MIN_AREA: {MIN_AREA}, MAX_AREA: {MAX_AREA}")


if __name__ == '__main__':
    image_path = "/media/general-max-riekeles/MMT_3/ME/ME_Biological/Data/New_Analysis/Lead_1/shortened_5seconds/ecoli_control_0h_sample1_rec1.tif_files_changed/raw/ecoli_control_0h_sample1_rec1_00000.tif"
    process_single_image(image_path)
