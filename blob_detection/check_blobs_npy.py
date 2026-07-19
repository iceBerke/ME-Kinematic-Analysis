# Checks the number of blobs in a specific npy file (user input) at a specific timepoint (user input)

# Script developed with the help of AI (Claude.AI)
# Last updated: 22/09/2025

import numpy as np

NPY_FILE_PATH = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09/segmentation_output/Lead_1/shortened_5seconds/ecoli_control_0h_sample1_rec1.tif_files_changed/blobs_ecoli_control_0h_sample1_rec1.tif_files_changed.npy"
TARGET_VALUE = 0  # Replace with the value you want to count in the third column


def count_rows_with_value(file_path, target_value):
    try:
        # Load the numpy array (read-only, won't modify the original file)
        data = np.load(file_path)

        # Check if the array has at least 3 columns
        if data.ndim < 2 or data.shape[1] < 3:
            print(f"Error: Array must have at least 3 columns. Current shape: {data.shape}")
            return 0

        # Count rows where the third column (index 2) equals the target value
        count = np.sum(data[:, 2] == target_value)

        return count

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return 0
    except Exception as e:
        print(f"Error loading file: {e}")
        return 0


# Main execution
if __name__ == "__main__":
    result = count_rows_with_value(NPY_FILE_PATH, TARGET_VALUE)
    print(f"Number of rows with value {TARGET_VALUE} in the third column: {result}")
