# Blob detection with sequential filtering and side-by-side visualization.

# This script detects both dark and bright blobs in a contrast-enhanced microscopy image
# using CLAHE preprocessing. It first filters blobs by minimum distance to avoid duplicates
# and other detection parameters from blob_parameters_check_v2.py (detection for 2048x2048 image size).

# Then, it groups blobs close to each other (within a proximity radius) and applies a
# sequential selection strategy for each group:
# 1) Select the blob with the lowest average intensity (darkest).
# 2) If multiple blobs have similarly low intensity, select the one with the largest size
#    and highest solidity (a measure of compactness defined as the ratio of contour area to
#    convex hull area).

# This method improves selection by prioritizing darkness, then shape and size quality,
# reducing potential false positives and duplicates in clustered blobs.

# The results are visualized side-by-side:
# - Left plot: blobs filtered only by minimum distance and other base parameters from blob_parameters_check_v2.py.
# - Right plot: blobs filtered by the sequential darkness and size/solidity criteria.

# Script developed with the help of AI (Claude.AI)
# Last updated: 20/09/2025

import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import os

# Calculate solidity from a contour:
# Solidity = contour area / area of convex hull (1 = fully solid convex shape)
def solidity(contour):
    area = cv.contourArea(contour)
    hull = cv.convexHull(contour)
    hull_area = cv.contourArea(hull)
    if hull_area == 0:
        return 0
    return float(area) / hull_area

# Extract contour of blob from local patch
def extract_blob_contour(img_gray, pt, size):
    x, y = int(pt[0]), int(pt[1])
    radius = int(size / 2)
    x1, y1 = max(x - radius, 0), max(y - radius, 0)
    x2, y2 = min(x + radius, img_gray.shape[1]-1), min(y + radius, img_gray.shape[0]-1)
    patch = img_gray[y1:y2, x1:x2]
    if patch.size == 0:
        return None, (x1, y1), None
    _, bw = cv.threshold(patch, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    contours, _ = cv.findContours(bw, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None, (x1, y1), patch
    center_rel = (radius, radius)
    best_cnt = max(contours, key=lambda c: cv.pointPolygonTest(c, center_rel, True))
    best_cnt += np.array([[x1, y1]])
    return best_cnt, (x1, y1), patch

# Group blobs by proximity radius
def group_keypoints_by_proximity(keypoints, radius):
    groups = []
    for kp in keypoints:
        pt = np.array(kp.pt)
        added = False
        for group in groups:
            if any(np.linalg.norm(pt - np.array(gkp.pt)) < radius for gkp in group):
                group.append(kp)
                added = True
                break
        if not added:
            groups.append([kp])
    return groups

# Sequential selection: 1) darkest blob; 2) largest + highest solidity among darkest
def sequential_select_blob(group, img_clahe):
    blobs_info = []
    for kp in group:
        contour, _, patch = extract_blob_contour(img_clahe, kp.pt, kp.size)
        if contour is None or patch is None:
            continue
        sol = solidity(contour)
        if sol == 0:
            continue
        mask = np.zeros(patch.shape, dtype=np.uint8)
        contour_shifted = contour - contour.min(axis=0)
        cv.drawContours(mask, [contour_shifted], -1, 255, -1)
        avg_intensity = cv.mean(patch, mask=mask)[0]
        blobs_info.append({'kp': kp, 'intensity': avg_intensity, 'solidity': sol, 'size': np.pi * (kp.size / 2) ** 2})

    if not blobs_info:
        # fallback: return first
        return group[0]

    intensities = np.array([b['intensity'] for b in blobs_info])
    min_intensity = intensities.min()
    # tolerance to select darkest candidates
    tolerance = 2.5
    darkest = [b for b in blobs_info if np.isclose(b['intensity'], min_intensity, atol=tolerance)]

    if len(darkest) == 1:
        return darkest[0]['kp']

    sizes = np.array([b['size'] for b in darkest])
    mollified_sizes = (sizes - sizes.min()) / (np.ptp(sizes) + 1e-6)

    solidities = np.array([b['solidity'] for b in darkest])
    mollified_solidities = solidities  # already [0..1]

    weights = {'size': 0.5, 'solidity': 0.5}
    combined_scores = weights['size'] * mollified_sizes + weights['solidity'] * mollified_solidities

    best_idx = np.argmax(combined_scores)
    return darkest[best_idx]['kp']

def detect_and_display_blobs_sequential_filtering(image_path,
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
                                                  bright_maxArea=800,
                                                  proximity_radius=25):
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None

    img = cv.imread(image_path, 0)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return None

    clahe = cv.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
    img_resized = cv.resize(img, (2048, 2048), interpolation=cv.INTER_LINEAR)
    img_clahe = clahe.apply(img_resized)

    params_dark = cv.SimpleBlobDetector_Params()
    params_dark.minThreshold = dark_minThreshold
    params_dark.maxThreshold = dark_maxThreshold
    params_dark.filterByArea = True
    params_dark.minArea = dark_minArea
    params_dark.maxArea = dark_maxArea
    params_dark.filterByCircularity = False
    params_dark.filterByConvexity = False
    params_dark.filterByInertia = False

    params_bright = cv.SimpleBlobDetector_Params()
    params_bright.minThreshold = bright_minThreshold
    params_bright.maxThreshold = bright_maxThreshold
    params_bright.filterByArea = True
    params_bright.minArea = bright_minArea
    params_bright.maxArea = bright_maxArea
    params_bright.filterByCircularity = False
    params_bright.filterByConvexity = False
    params_bright.filterByInertia = False

    detector_dark = cv.SimpleBlobDetector_create(params_dark)
    detector_bright = cv.SimpleBlobDetector_create(params_bright)

    keypoints_dark = detector_dark.detect(img_clahe)
    img_inverted = cv.bitwise_not(img_clahe)
    keypoints_bright = detector_bright.detect(img_inverted)

    keypoints = keypoints_dark + keypoints_bright

    filtered_keypoints = []
    for kp in keypoints:
        if all(np.linalg.norm(np.array(kp.pt) - np.array(k.pt)) >= min_distance for k in filtered_keypoints):
            filtered_keypoints.append(kp)

    groups = group_keypoints_by_proximity(filtered_keypoints, proximity_radius)
    filtered_final_keypoints = []
    for group in groups:
        if len(group) == 1:
            filtered_final_keypoints.append(group[0])
        else:
            best_kp = sequential_select_blob(group, img_clahe)
            filtered_final_keypoints.append(best_kp)

    def draw_keypoints(image, keypoints):
        img_display = cv.cvtColor(image, cv.COLOR_GRAY2RGB)
        for kp in keypoints:
            center = (int(kp.pt[0]), int(kp.pt[1]))
            radius = int(kp.size / 2)
            cv.circle(img_display, center, radius + 2, (255, 165, 0), 2)
            cv.circle(img_display, center, radius, (255, 140, 0), 1)
        return img_display

    img_orig_disp = draw_keypoints(img_clahe, filtered_keypoints)
    img_filtered_disp = draw_keypoints(img_clahe, filtered_final_keypoints)

    dark_count = len(keypoints_dark)
    bright_count = len(keypoints_bright)
    total_raw = len(filtered_keypoints)
    total_filtered = len(filtered_final_keypoints)

    print(f"Detected blobs in {os.path.basename(image_path)}:")
    print(f"  Dark blobs: {dark_count}")
    print(f"  Bright blobs: {bright_count}")
    print(f"  Total filtered by distance only: {total_raw}")
    print(f"  Total after sequential filtering: {total_filtered}")

    fig, axs = plt.subplots(1, 2, figsize=(16, 16))
    axs[0].imshow(img_orig_disp)
    axs[0].set_title(f'Original blobs (distance filter)\nTotal: {total_raw}')
    axs[0].axis('off')

    axs[1].imshow(img_filtered_disp)
    axs[1].set_title('Filtered blobs (sequential: darkness, size+solidity)')
    axs[1].axis('off')

    plt.tight_layout()
    plt.show()

    return {
        'keypoints_dark': keypoints_dark,
        'keypoints_bright': keypoints_bright,
        'filtered_keypoints_distance': filtered_keypoints,
        'filtered_keypoints_final': filtered_final_keypoints,
        'dark_count': dark_count,
        'bright_count': bright_count,
        'total_raw_filtered_distance': total_raw,
        'total_filtered_final': total_filtered
    }


if __name__ == "__main__":
    image_path = "/media/general-max-riekeles/MMT_3/ME/ME_part2/Data/Nickel_4/shortened_5seconds/ecoli_control_24h_sample1_rec1.tif_files_changed/raw/ecoli_control_24h_sample1_rec1_00000.tif"
    if os.path.exists(image_path):
        print(f"Processing image: {image_path}")
        detect_and_display_blobs_sequential_filtering(image_path)
    else:
        print(f"Error: Image not found at {image_path}")
