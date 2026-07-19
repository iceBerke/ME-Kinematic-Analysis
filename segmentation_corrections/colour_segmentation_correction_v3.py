# Advanced methods to separate connected track segments
# For cases where simple connected components doesn't work because segments are physically connected

# Script developed with the help of AI (Claude.AI)
# Last updated: 16/09/2025

import cv2 as cv
import numpy as np
from pathlib import Path
from scipy import ndimage
from skimage.morphology import skeletonize, medial_axis
from skimage.measure import label
import matplotlib.pyplot as plt


def separate_by_skeleton_analysis(image_path, min_area=50):
    """
    Method 1: Use skeleton analysis to find branch points and separate tracks
    """
    input_path = Path(image_path)
    image = cv.imread(str(input_path), cv.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    print(f"Processing with skeleton analysis: {input_path.name}")

    # Convert to binary
    _, binary = cv.threshold(image, 127, 255, cv.THRESH_BINARY)
    binary_bool = binary > 0

    # Create skeleton
    skeleton = skeletonize(binary_bool)

    # Find branch points (pixels with more than 2 neighbors)
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]], dtype=np.uint8)

    # Count neighbors for each skeleton pixel
    neighbor_count = cv.filter2D(skeleton.astype(np.uint8), -1, kernel)
    skeleton_pixels = skeleton.astype(np.uint8)
    neighbor_count = neighbor_count * skeleton_pixels

    # Branch points have more than 2 neighbors
    branch_points = (neighbor_count > 2) & skeleton

    if np.any(branch_points):
        print(f"Found {np.sum(branch_points)} branch points")

        # Remove branch points from original binary image to disconnect segments
        binary_disconnected = binary.copy()

        # Dilate branch points slightly to ensure disconnection
        branch_dilated = cv.dilate(branch_points.astype(np.uint8), np.ones((3, 3)), iterations=1)
        binary_disconnected[branch_dilated > 0] = 0

        # Now find connected components
        num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(binary_disconnected, connectivity=8)

        return save_components(input_path, labels, stats, num_labels, min_area, "skeleton")
    else:
        print("No branch points found - trying erosion method")
        return separate_by_erosion(image_path, min_area)


def separate_by_erosion(image_path, min_area=50, erosion_iterations=2):
    """
    Method 2: Use erosion to break thin connections between segments
    """
    input_path = Path(image_path)
    image = cv.imread(str(input_path), cv.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    print(f"Processing with erosion method: {input_path.name}")

    # Convert to binary
    _, binary = cv.threshold(image, 127, 255, cv.THRESH_BINARY)

    # Apply erosion to break thin connections
    kernel = np.ones((3, 3), np.uint8)
    eroded = cv.erode(binary, kernel, iterations=erosion_iterations)

    # Find connected components in eroded image
    num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(eroded, connectivity=8)

    # Filter small components
    valid_labels = []
    for i in range(1, num_labels):
        if stats[i, cv.CC_STAT_AREA] >= min_area:
            valid_labels.append(i)

    if len(valid_labels) > 1:
        print(f"Found {len(valid_labels)} components after erosion")

        # For each valid component, dilate back to original size using original image as mask
        output_paths = []
        for idx, label_id in enumerate(valid_labels, 1):
            # Get the eroded component
            component_mask = (labels == label_id).astype(np.uint8)

            # Dilate back, but constrain to original binary image
            dilated = component_mask.copy()
            for _ in range(erosion_iterations + 1):  # Dilate a bit more to recover
                dilated = cv.dilate(dilated, kernel, iterations=1)
                dilated = cv.bitwise_and(dilated, binary // 255)  # Constrain to original shape

            # Save component
            output_filename = f"{input_path.stem}_erosion_{idx}{input_path.suffix}"
            output_path = input_path.parent / output_filename

            success = cv.imwrite(str(output_path), dilated * 255)
            if success:
                output_paths.append(str(output_path))
                print(f"Saved component {idx}: {output_filename}")

        return output_paths
    else:
        print("Erosion didn't separate components - trying directional analysis")
        return separate_by_direction_change(image_path, min_area)


def separate_by_direction_change(image_path, min_area=50, angle_threshold=45):
    """
    Method 3: Analyze direction changes to find separation points
    """
    input_path = Path(image_path)
    image = cv.imread(str(input_path), cv.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    print(f"Processing with direction analysis: {input_path.name}")

    # Convert to binary
    _, binary = cv.threshold(image, 127, 255, cv.THRESH_BINARY)

    # Get contours
    contours, _ = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

    if len(contours) == 0:
        print("No contours found")
        return []

    # Use the largest contour
    contour = max(contours, key=cv.contourArea)
    contour = contour.reshape(-1, 2)

    if len(contour) < 10:
        print("Contour too small for direction analysis")
        return []

    # Calculate direction changes along the contour
    directions = []
    window_size = 5

    for i in range(window_size, len(contour) - window_size):
        # Get points before and after current point
        p1 = contour[i - window_size]
        p2 = contour[i + window_size]

        # Calculate direction vector
        direction = np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
        directions.append((i, direction))

    # Find sharp direction changes
    separation_points = []
    for i in range(1, len(directions)):
        angle_diff = abs(directions[i][1] - directions[i - 1][1])
        # Handle angle wrapping
        angle_diff = min(angle_diff, 2 * np.pi - angle_diff)
        angle_diff_degrees = np.degrees(angle_diff)

        if angle_diff_degrees > angle_threshold:
            separation_points.append(contour[directions[i][0]])

    if separation_points:
        print(f"Found {len(separation_points)} potential separation points")

        # Create separation by drawing small circles at separation points
        binary_separated = binary.copy()
        for point in separation_points:
            cv.circle(binary_separated, tuple(point), 3, 0, -1)  # Draw black circle

        # Find connected components after separation
        num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(binary_separated, connectivity=8)

        return save_components(input_path, labels, stats, num_labels, min_area, "direction")
    else:
        print("No significant direction changes found - trying manual coordinate separation")
        return separate_by_coordinates(image_path, min_area)


def separate_by_coordinates(image_path, min_area=50):
    """
    Method 4: Separate based on coordinate analysis (find the junction manually)
    """
    input_path = Path(image_path)
    image = cv.imread(str(input_path), cv.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    print(f"Processing with coordinate analysis: {input_path.name}")

    # Convert to binary
    _, binary = cv.threshold(image, 127, 255, cv.THRESH_BINARY)

    # Find all white pixel coordinates
    white_pixels = np.where(binary > 0)
    coords = list(zip(white_pixels[1], white_pixels[0]))  # (x, y) format

    if len(coords) < 10:
        print("Not enough pixels for analysis")
        return []

    # Find the center of mass
    center_x = np.mean([c[0] for c in coords])
    center_y = np.mean([c[1] for c in coords])

    print(f"Center of mass: ({center_x:.1f}, {center_y:.1f})")

    # Find the pixel closest to center - likely junction point
    distances = [(abs(c[0] - center_x) + abs(c[1] - center_y), c) for c in coords]
    distances.sort()
    junction_point = distances[0][1]

    print(f"Estimated junction point: {junction_point}")

    # Remove pixels around junction point
    binary_separated = binary.copy()
    cv.circle(binary_separated, junction_point, 4, 0, -1)  # Remove 4-pixel radius around junction

    # Find connected components
    num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(binary_separated, connectivity=8)

    return save_components(input_path, labels, stats, num_labels, min_area, "coordinate")


def save_components(input_path, labels, stats, num_labels, min_area, method_name):
    """Helper function to save separated components"""
    output_paths = []
    segment_count = 0

    print(f"Found {num_labels - 1} connected components")

    for i in range(1, num_labels):
        area = stats[i, cv.CC_STAT_AREA]

        if area < min_area:
            print(f"Skipping component {i} (area: {area} < {min_area})")
            continue

        # Create mask for this component only
        component_mask = (labels == i).astype(np.uint8) * 255

        # Create output filename
        segment_count += 1
        output_filename = f"{input_path.stem}_{method_name}_{segment_count}{input_path.suffix}"
        output_path = input_path.parent / output_filename

        # Save the segment
        success = cv.imwrite(str(output_path), component_mask)

        if success:
            output_paths.append(str(output_path))
            print(f"Saved segment {segment_count}: {output_filename} (area: {area})")
        else:
            print(f"Failed to save segment {segment_count}: {output_filename}")

    return output_paths


def separate_connected_tracks(image_path, min_area=50):
    """
    Main function that tries different methods in sequence
    """
    print("=" * 50)
    print("Advanced Track Separation")
    print("=" * 50)

    try:
        # Try skeleton analysis first
        result = separate_by_skeleton_analysis(image_path, min_area)
        if len(result) > 1:
            return result

        # If that doesn't work, try erosion
        result = separate_by_erosion(image_path, min_area)
        if len(result) > 1:
            return result

        # Try direction change analysis
        result = separate_by_direction_change(image_path, min_area)
        if len(result) > 1:
            return result

        # Finally try coordinate analysis
        result = separate_by_coordinates(image_path, min_area)
        return result

    except Exception as e:
        print(f"Error during separation: {e}")
        return []


if __name__ == "__main__":
    # Replace with your image path
    image_path = "/media/berke-dhm/MMT_3/ME/ME_part2/Data/segmentation_output/Nickel_1/shortened_5seconds/ecoli_control_1h_sample1_rec3.tif_files_changed/t13.png"

    try:
        output_files = separate_connected_tracks(image_path, min_area=50)

        if output_files:
            print(f"\nSuccess! Created {len(output_files)} separated files:")
            for file_path in output_files:
                print(f"  - {file_path}")
        else:
            print("\nNo separation achieved. The image might contain a single continuous track.")

    except Exception as e:
        print(f"Error: {e}")