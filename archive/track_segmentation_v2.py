import cv2 as cv
import numpy as np
import os

def process_image_for_tracks(image_path, colors, output_folder, min_area=10):
    """
    Process an image to extract tracks of specified colors, remove isolated points, and save the results.
    """
    original_image = cv.imread(image_path, cv.IMREAD_COLOR)
    if original_image is None:
        raise ValueError(f"Image not loaded properly: {image_path}")

    print(f"Image loaded: {image_path}")
    print(f"Image shape: {original_image.shape}")
    print(f"Image dtype: {original_image.dtype}")

    image_base_name = os.path.splitext(os.path.basename(image_path))[0]
    track_counter = 1

    for color in colors:
        color_np = np.array(color[::-1], dtype=np.uint8)
        print(f"Processing color: {color_np[::-1]}")

        mask = cv.inRange(original_image, color_np, color_np)
        non_zero_count = np.count_nonzero(mask)
        print(f"Non-zero pixels in mask for color {color}: {non_zero_count}")

        if non_zero_count > 0:
            # Remove small objects (isolated points)
            nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask, connectivity=8)
            sizes = stats[1:, -1]
            nb_components = nb_components - 1

            img2 = np.zeros((output.shape))
            for i in range(0, nb_components):
                if sizes[i] >= min_area:
                    img2[output == i + 1] = 255

            # Create the final track image
            track_image = np.zeros_like(original_image)
            track_image[img2 > 0] = [255, 255, 255]  # Draw the track in white

            track_image_path = os.path.join(output_folder, f"t{track_counter}.png")
            cv.imwrite(track_image_path, track_image)

            print(f"Saved {track_image_path}")
            track_counter += 1
        else:
            print(f"No pixels detected for color {color}")

    print(f"Processing complete for image: {image_path}")

def process_all_images(parent_directory, colors, min_area=10):
    output_folder = os.path.join(parent_directory, "tracks")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(parent_directory):
        if file_name.lower().endswith('.tif') and "median_image" not in file_name.lower():
            image_path = os.path.join(parent_directory, file_name)
            try:
                process_image_for_tracks(image_path, colors, output_folder, min_area)
            except ValueError as e:
                print(e)

# Usage
parent_directory = "/media/berke-dhm/MMT_3/ME/ME_part2/ME_24_11/Copper_3/shortened_10seconds/ecoli_cu10_0h_sample3_rec2.tif_files_changed/validate"
colors = [
    (254, 209, 209),
    (226, 209, 209),
    (211, 209, 209),
    (189, 209, 209),
    (171, 209, 209),
    (145, 209, 209),
    (1, 209, 209),
    (254, 254, 254),
    (254, 231, 254),
    (254, 220, 254),
    (254, 204, 254),
    (254, 182, 254),
    (254, 254, 236),
    (254, 254, 220),
    (254, 254, 203),
    (254, 254, 184),
    (254, 254, 160),
    (254, 254, 1),
    (226, 254, 254),
    (211, 254, 254),
    (189, 254, 254),
    (171, 254, 254),
    (145, 254, 254),
    (1, 254, 254),
    (1, 182, 254),
    (1, 220, 254),
    (1, 254, 1),
    (1, 254, 184),
    (254, 182, 1),
    (189, 182, 1),
    (214, 214, 214),
    (214, 254, 214),
    (214, 253, 214),
    (214, 250, 214),
    (214, 249, 214),
    (214, 248, 214),
    (214, 246, 214),
    (214, 245, 214),
    (214, 244, 214),
    (214, 242, 214),
    (214, 241, 214),
    (214, 240, 214),
    (214, 236, 214),
    (214, 232, 214),
    (214, 229, 214),
    (214, 228, 214),
    (214, 225, 214),
    (214, 224, 214),
    (214, 221, 214),
    (214, 217, 214),
    (214, 214, 254),
    (214, 214, 253),
    (214, 214, 250),
    (214, 214, 249),
    (214, 214, 246),
    (214, 214, 245),
    (214, 214, 242),
    (214, 214, 241),
    (214, 214, 238),
    (214, 214, 229),
    (214, 214, 225),
    (214, 214, 221),
    (214, 214, 217),
    (214, 214, 209),
    (214, 214, 199),
    (214, 214, 181),
    (214, 214, 179)
]

process_all_images(parent_directory, colors, min_area=10)
