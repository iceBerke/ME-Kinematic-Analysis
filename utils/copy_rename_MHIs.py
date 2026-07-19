import os
import shutil

def rename_and_move_tif_files(parent_directory):
    """
    Rename .tif files by using the part before the first dot and appending '_tracks',
    then move them to a 'coloured_MHIs' subfolder within the parent directory.
    """
    # Ensure the parent directory exists
    if not os.path.isdir(parent_directory):
        raise ValueError(f"The directory {parent_directory} does not exist.")

    # Create the 'coloured_MHIs' subfolder within the parent directory
    output_folder = os.path.join(parent_directory, "coloured_MHIs")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder: {output_folder}")

    # Iterate over all files in the parent directory
    for file_name in os.listdir(parent_directory):
        # Construct the full file path
        file_path = os.path.join(parent_directory, file_name)

        # Skip directories
        if os.path.isdir(file_path):
            print(f"Skipped directory: {file_path}")
            continue

        # Split the file name and extension
        root, ext = os.path.splitext(file_name)

        # Process only .tif files
        if ext.lower() == '.tif':
            # Extract the base name before the first dot
            base_name = root.split('.', 1)[0]

            # Construct the new file name with '_tracks' and the same extension
            new_file_name = f"{base_name}_tracks{ext}"
            new_file_path = os.path.join(output_folder, new_file_name)

            # Move the file to the 'coloured_MHIs' folder with the new name
            shutil.copy(file_path, new_file_path)

            print(f"Copied and renamed {file_name} to {new_file_name} in {output_folder}")
        else:
            print(f"Skipped non-TIF file: {file_name}")

    print("Renaming and moving complete!")

# Example usage
parent_directory = "/home/berke-dhm/Desktop/MHI_colour_test"  # Path to the parent directory
rename_and_move_tif_files(parent_directory)
