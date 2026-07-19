# Separate different tracks from a same image and save them in the same folder with _1, _2, etc. suffixes
# Groups nearby components that belong to the same track
# Input just needs to be the path of the image

# Script developed with the help of AI (Claude.AI)
# Last update: 14/09/2025

import cv2 as cv
import numpy as np
from pathlib import Path
from sklearn.cluster import DBSCAN


def separate_tracks_with_grouping(image_path, min_area, grouping_distance):
    # Convert to Path object for easier handling
    input_path = Path(image_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    # Read the image
    image = cv.imread(str(input_path), cv.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    print(f"Processing: {input_path.name}")

    # Convert to binary if not already
    _, binary = cv.threshold(image, 127, 255, cv.THRESH_BINARY)

    # Find connected components
    num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(binary, connectivity=8)

    print(f"Found {num_labels - 1} connected components")

    # Filter components by area and collect valid ones
    valid_components = []
    for i in range(1, num_labels):
        area = stats[i, cv.CC_STAT_AREA]
        if area >= min_area:
            valid_components.append({
                'label': i,
                'centroid': centroids[i],
                'area': area,
                'stats': stats[i]
            })
        else:
            print(f"Skipping component {i} (area: {area} < {min_area})")

    if len(valid_components) == 0:
        print("No valid components found")
        return []

    print(f"Found {len(valid_components)} valid components")

    # Group components by proximity using DBSCAN clustering
    if len(valid_components) > 1:
        # Extract centroids for clustering
        centroids_array = np.array([comp['centroid'] for comp in valid_components])

        # Use DBSCAN to group nearby components
        # eps is the maximum distance between points in the same cluster
        # min_samples=1 means a single point can form a cluster
        clustering = DBSCAN(eps=grouping_distance, min_samples=1).fit(centroids_array)

        # Group components by cluster labels
        groups = {}
        for idx, cluster_label in enumerate(clustering.labels_):
            if cluster_label not in groups:
                groups[cluster_label] = []
            groups[cluster_label].append(valid_components[idx])

        print(f"Grouped {len(valid_components)} components into {len(groups)} tracks")
    else:
        # Only one component, so it's one track
        groups = {0: valid_components}
        print("Only one component found, creating single track")

    # Get file parts for naming
    parent_folder = input_path.parent
    file_stem = input_path.stem
    file_ext = input_path.suffix

    output_paths = []
    track_count = 0

    # Create an image for each track (group)
    for group_id, components in groups.items():
        track_count += 1

        # Create a mask that includes all components in this track
        track_mask = np.zeros_like(labels, dtype=np.uint8)
        total_area = 0

        for comp in components:
            component_mask = (labels == comp['label'])
            track_mask[component_mask] = 255
            total_area += comp['area']

        # Create output filename
        output_filename = f"{file_stem}_{track_count}{file_ext}"
        output_path = parent_folder / output_filename

        # Save the track
        success = cv.imwrite(str(output_path), track_mask)

        if success:
            output_paths.append(str(output_path))
            component_labels = [comp['label'] for comp in components]
            print(f"Saved track {track_count}: {output_filename}")
            print(f"  - Combined components: {component_labels}")
            print(f"  - Total area: {total_area}")
        else:
            print(f"Failed to save track {track_count}: {output_filename}")

    print(f"Created {len(output_paths)} track images from {len(valid_components)} components")
    return output_paths

# Keep the original function for backward compatibility
def separate_tracks_simple(image_path, min_area=25):
    # [Original function code remains the same]
    input_path = Path(image_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    image = cv.imread(str(input_path), cv.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    print(f"Processing: {input_path.name}")

    _, binary = cv.threshold(image, 127, 255, cv.THRESH_BINARY)
    num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(binary, connectivity=8)

    parent_folder = input_path.parent
    file_stem = input_path.stem
    file_ext = input_path.suffix

    output_paths = []
    segment_count = 0

    print(f"Found {num_labels - 1} connected components")

    for i in range(1, num_labels):
        area = stats[i, cv.CC_STAT_AREA]

        if area < min_area:
            print(f"Skipping component {i} (area: {area} < {min_area})")
            continue

        component_mask = (labels == i).astype(np.uint8) * 255

        segment_count += 1
        output_filename = f"{file_stem}_{segment_count}{file_ext}"
        output_path = parent_folder / output_filename

        success = cv.imwrite(str(output_path), component_mask)

        if success:
            output_paths.append(str(output_path))
            print(f"Saved segment {segment_count}: {output_filename} (area: {area})")
        else:
            print(f"Failed to save segment {segment_count}: {output_filename}")

    print(f"Created {len(output_paths)} segment images")
    return output_paths


# Example usage:
if __name__ == "__main__":
    image_path = "/media/berke-dhm/MMT_3/ME/ME_Biological/Data/New_Analysis/segmentation_output/Zinc_3/shortened_5seconds/ecoli_control_0h_sample1_rec2.tif_files_changed/t10.png"

    try:
        output_files = separate_tracks_with_grouping(
            image_path,
            min_area=10,
            grouping_distance=200
        )
        print(f"\nSuccess! Created {len(output_files)} track files:")
        for file_path in output_files:
            print(f"  - {file_path}")
    except Exception as e:
        print(f"Error: {e}")