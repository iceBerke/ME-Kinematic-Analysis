# Python script used to copy coloured MHIs (i.e., for segmentation) and original MHIs if there is no coloured version
# into a new directory
# Developed with the help of AI (Perplexity.AI)

# Last edit: 05/08/2025

from pathlib import Path
import shutil

def copy_images(src_dir, dest_dir):
    src_path = Path(src_dir)
    dest_path = Path(dest_dir)

    if not src_path.exists() or not src_path.is_dir():
        raise ValueError(f"Source directory {src_dir} does not exist or is not a directory")

    dest_path.mkdir(parents=True, exist_ok=True)

    for folder in src_path.iterdir():
        if not folder.is_dir():
            continue
        validate_folder = folder / 'validate'
        if validate_folder.exists() and validate_folder.is_dir():
            dest_subfolder = dest_path / folder.name
            dest_subfolder.mkdir(parents=True, exist_ok=True)
            # Copy all _color.tif files, or _mhi.png if none found
            color_tifs = list(validate_folder.glob('*_color.tif'))
            if color_tifs:
                for tif in color_tifs:
                    shutil.copy2(tif, dest_subfolder)
            else:
                mhi_pngs = list(validate_folder.glob('*_mhi.png'))
                for png in mhi_pngs:
                    shutil.copy2(png, dest_subfolder)

# Example usage:
src_directory = '/media/berke-dhm/MMT_3/ME/ME_part2/ME_24_11/Copper_4/shortened_10seconds'       # Change this to your input directory
dest_directory = '/media/berke-dhm/MMT_3/ME/ME_part2/ME_24_11/Max_05_08_2025/Copper_4_shortened_10seconds'     # Change this to your output directory

copy_images(src_directory, dest_directory)
