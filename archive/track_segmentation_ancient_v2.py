import cv2 as cv
import numpy as np
import os

def process_image_for_tracks(image_path, colors, output_folder):
    """
    Process an image to extract tracks of specified colors and save the results.
    """
    # Read the original image
    original_image = cv.imread(image_path, cv.IMREAD_COLOR)

    # Check if the image was loaded properly
    if original_image is None:
        raise ValueError(f"Image not loaded properly: {image_path}")

    # Check image properties
    print(f"Image loaded: {image_path}")
    print(f"Image shape: {original_image.shape}")
    print(f"Image dtype: {original_image.dtype}")

    # Get the base name of the image for output naming
    image_base_name = os.path.splitext(os.path.basename(image_path))[0]

    # Counter for naming output images
    track_counter = 1

    # Process each color
    for color in colors:
        # Convert color to NumPy array of type uint8 and ensure it's in BGR format for OpenCV
        color_np = np.array(color[::-1], dtype=np.uint8)
        print(f"Processing color: {color_np[::-1]}")  # Print original RGB color

        # Create a mask for the current color
        mask = cv.inRange(original_image, color_np, color_np)

        # Check how many non-zero pixels are in the mask
        non_zero_count = np.count_nonzero(mask)
        print(f"Non-zero pixels in mask for color {color}: {non_zero_count}")

        # If the color is detected, create and save the output image
        if non_zero_count > 0:
            # Create a new image with the current track color drawn in white
            track_image = np.zeros_like(original_image)
            track_image[mask > 0] = [255, 255, 255]  # Draw the track in white

            # Save the resulting image directly in the output folder with sequential naming
            track_image_path = os.path.join(output_folder, f"t{track_counter}.png")
            cv.imwrite(track_image_path, track_image)

            print(f"Saved {track_image_path}")

            # Increment the counter
            track_counter += 1
        else:
            print(f"No pixels detected for color {color}")

    print(f"Processing complete for image: {image_path}")

def process_all_images(parent_directory, colors):
    """
    Process all TIFF images in the parent directory and save the results in the tracks folder.
    """
    # Create the 'tracks' subfolder in the parent directory
    output_folder = os.path.join(parent_directory, "tracks")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over all TIFF images in the parent directory
    for file_name in os.listdir(parent_directory):
        if file_name.lower().endswith('.tif') and "median_image" not in file_name.lower():
            image_path = os.path.join(parent_directory, file_name)
            try:
                process_image_for_tracks(image_path, colors, output_folder)
            except ValueError as e:
                print(e)

# Example usage
parent_directory = "path"  # Path to the parent directory
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
    (189, 182, 1)
]

process_all_images(parent_directory, colors)
