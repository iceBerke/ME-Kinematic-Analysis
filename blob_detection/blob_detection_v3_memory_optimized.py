# Batch blob detector for both dark and bright blobs with NPY output
# Enhanced version with brightness and solidity parameters
# 
# PURPOSE:
# This script performs automated blob detection on time-series microscopy images stored in a complex
# directory structure. It detects both dark and bright circular features (blobs) in .tif images and
# saves the results as NumPy arrays containing x,y coordinates, timepoints, blob sizes, brightness, and solidity.
# The script is designed for high-throughput analysis of bacterial tracking experiments.
#
# DIRECTORY STRUCTURE EXPECTED:
# root_directory/
# ├── segmentation_output/                    <- Output folder (created/used by this script)
# │   ├── subfolder_1/                       <- Mirrors data folder structure
# │   │   └── shortened_X/                   <- Matches shortened folders in data
# │   │       └── subsubfolder_1/            <- Matches data subsubfolders
# │   │           ├── npy_tracks/            <- Existing tracking data (optional)
# │   │           └── blobs_subsubfolder_1.npy <- NPY FILES SAVED HERE
# │   └── subfolder_2/
# │       └── shortened_Y/
# │           └── subsubfolder_2/
# │               └── blobs_subsubfolder_2.npy
# └── subfolder_1/                           <- Data folders (input)
#     └── shortened_X/                       <- Time-series experiment folders
#         └── subsubfolder_1/                <- Individual recording sessions
#             ├── raw/                       <- IMAGES TO PROCESS (.tif files)
#             │   ├── image_00000.tif       <- Timepoint 0
#             │   ├── image_00001.tif       <- Timepoint 1
#             │   └── ...
#             └── other_folders/             <- Other processing outputs (ignored)
#
# OUTPUT FORMAT:
# Each NPY file contains an array with shape (n_blobs, 6) where columns are:
# [x_coordinate, y_coordinate, timepoint, blob_area, brightness, solidity]
#
# NEW PARAMETERS:
# - blob_area: Area of the blob in pixels² (calculated as π × (diameter/2)²)
# - brightness: Average pixel intensity within the blob contour (0-255)
# - solidity: Ratio of contour area to convex hull area (0-1, where 1 = perfectly convex)
#
# FILE STRUCTURE: One NPY file per subsubfolder containing ALL timepoints from that experiment.
# This is efficient for time-series analysis - a typical experiment with 30+ images and ~200 blobs 
# per image will result in ~6000+ blobs in a single file (~300KB), which is optimal for loading 
# and analyzing temporal patterns.
#
# IMAGE PROCESSING: All images are resized to 2048x2048 pixels before blob detection, regardless 
# of original image dimensions. This means:
# - Blob coordinates are ALWAYS relative to 2048x2048 space
# - Original image aspect ratios may be distorted if not square
# - Provides consistent coordinate system across different experiments
# - If original images differ significantly from 2048x2048, consider modifying resize behavior
#
# PARAMETERS:
# Adjustable parameters include min/max area thresholds for both dark and bright blobs,
# CLAHE preprocessing settings, and minimum distance filtering between detected blobs.
# All parameters are hard-coded in the main section below - no command line interface.

# Script developed with the help of AI (Claude.AI)
# Last updated: 20/09/2025

# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de

# Memory-optimized version of the blob detector
# Key improvements for memory efficiency

import cv2 as cv
import numpy as np
import re
from pathlib import Path
import glob
import gc  # Garbage collector for explicit memory cleanup

def calculate_blob_properties_efficient(img_clahe, kp):
    """Calculate brightness and solidity for a single blob - memory efficient version"""
    x, y = int(kp.pt[0]), int(kp.pt[1])
    radius = int(kp.size / 2)
    
    # Extract only the necessary patch from the image
    x1, y1 = max(x - radius, 0), max(y - radius, 0)
    x2, y2 = min(x + radius, img_clahe.shape[1]), min(y + radius, img_clahe.shape[0])
    
    # Handle edge cases with zero patch size only
    if x2 - x1 == 0 or y2 - y1 == 0:
        return float(img_clahe[y, x]), 0.0
    
    patch = img_clahe[y1:y2, x1:x2].copy()
    
    brightness = float(np.mean(patch))
    solidity_value = 0.0
    
    try:
        _, binary = cv.threshold(patch, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        contours, _ = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            best_contour = max(contours, key=cv.contourArea)
            area = cv.contourArea(best_contour)
            if area > 0:
                hull = cv.convexHull(best_contour)
                hull_area = cv.contourArea(hull)
                solidity_value = float(area / hull_area) if hull_area > 0 else 0.0
            
            try:
                mask = np.zeros(patch.shape, dtype=np.uint8)
                cv.drawContours(mask, [best_contour], -1, 255, -1)
                masked_pixels = patch[mask > 0]
                if len(masked_pixels) > 0:
                    brightness = float(np.mean(masked_pixels))
                # Explicit cleanup
                del mask, masked_pixels
            except:
                pass
        
        # Explicit cleanup
        del binary, contours
        if 'best_contour' in locals():
            del best_contour
        if 'hull' in locals():
            del hull
            
    except Exception as e:
        print(f"Warning: Error in blob property calculation: {e}")
    
    finally:
        del patch
    
    return brightness, solidity_value

def detect_blobs_single_image(image_path, **params):
    """Memory-optimized blob detection for single image"""
    
    # Load image in grayscale
    img = cv.imread(str(image_path), 0)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return None

    try:
        # Apply CLAHE and resize
        clahe = cv.createCLAHE(clipLimit=params['clipLimit'], 
                              tileGridSize=params['tileGridSize'])
        img_resized = cv.resize(img, (2048, 2048), interpolation=cv.INTER_LINEAR)
        
        # Clear original image immediately after resizing
        del img
        
        img_clahe = clahe.apply(img_resized)
        
        # Clear resized image immediately after CLAHE
        del img_resized, clahe

        # Setup blob detector parameters for DARK blobs
        params_dark = cv.SimpleBlobDetector_Params()
        params_dark.minThreshold = params['dark_minThreshold']
        params_dark.maxThreshold = params['dark_maxThreshold']
        params_dark.filterByArea = True
        params_dark.minArea = params['dark_minArea']
        params_dark.maxArea = params['dark_maxArea']
        params_dark.filterByCircularity = False
        params_dark.filterByConvexity = False
        params_dark.filterByInertia = False

        # Setup blob detector parameters for BRIGHT blobs
        params_bright = cv.SimpleBlobDetector_Params()
        params_bright.minThreshold = params['bright_minThreshold']
        params_bright.maxThreshold = params['bright_maxThreshold']
        params_bright.filterByArea = True
        params_bright.minArea = params['bright_minArea']
        params_bright.maxArea = params['bright_maxArea']
        params_bright.filterByCircularity = False
        params_bright.filterByConvexity = False
        params_bright.filterByInertia = False

        # Create detectors
        detector_dark = cv.SimpleBlobDetector_create(params_dark)
        detector_bright = cv.SimpleBlobDetector_create(params_bright)

        # Detect dark blobs on CLAHE image
        keypoints_dark = detector_dark.detect(img_clahe)

        # Detect bright blobs on inverted CLAHE image
        img_inverted = cv.bitwise_not(img_clahe)
        keypoints_bright = detector_bright.detect(img_inverted)

        # Clear inverted image immediately after detection
        del img_inverted, detector_dark, detector_bright

        # Combine all keypoints
        keypoints = keypoints_dark + keypoints_bright
        del keypoints_dark, keypoints_bright

        # Filter keypoints by minimum distance
        filtered_keypoints = []
        for kp in keypoints:
            if all(np.linalg.norm(np.array(kp.pt) - np.array(k.pt)) >= params['min_distance'] 
                   for k in filtered_keypoints):
                filtered_keypoints.append(kp)
        
        del keypoints

        # Process blobs and extract data
        blob_data_list = []
        for kp in filtered_keypoints:
            brightness, sol = calculate_blob_properties_efficient(img_clahe, kp)
            area = np.pi * (kp.size / 2) ** 2
            blob_data = [kp.pt[0], kp.pt[1], area, brightness, sol]
            blob_data_list.append(blob_data)
    
    finally:
        # Ensure cleanup even if exceptions occur
        if 'img_clahe' in locals():
            del img_clahe
        if 'filtered_keypoints' in locals():
            del filtered_keypoints
        
        # Force garbage collection
        gc.collect()
    
    return blob_data_list

def extract_timepoint_from_filename(filename):
    """Extract timepoint from filename"""
    match = re.search(r'_(\d+)(?:\.\w+)?$', filename)
    if match:
        return int(match.group(1))
    else:
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return int(numbers[-1])
        else:
            return 0

def process_batch_blob_detection(root_directory,
                                segmentation_folder_name="segmentation_output",
                                subfolder_parameters=None,
                                default_parameters=None,
                                max_images_per_batch=50):  # NEW: Batch size limit
    """
    Memory-optimized batch processing with periodic cleanup and error tracking
    max_images_per_batch: Process images in smaller batches to prevent memory buildup
    """
    
    # Initialize tracking variables
    processing_summary = {
        'successful_subfolders': [],
        'failed_subfolders': [],
        'skipped_subfolders': [],
        'successful_experiments': [],
        'failed_experiments': [],
        'total_images_processed': 0,
        'total_blobs_detected': 0,
        'errors': []
    }
    
    if default_parameters is None:
        default_parameters = {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 90,
            'bright_maxThreshold': 255,
            'bright_minArea': 35,
            'bright_maxArea': 800
        }
    
    if subfolder_parameters is None:
        subfolder_parameters = {}
    
    root_path = Path(root_directory)
    segmentation_path = root_path / segmentation_folder_name
    
    if not segmentation_path.exists():
        error_msg = f"Error: Segmentation folder not found at {segmentation_path}"
        print(error_msg)
        processing_summary['errors'].append(error_msg)
        return processing_summary
    
    # Process each subfolder in segmentation_output
    for subfolder in segmentation_path.iterdir():
        if not subfolder.is_dir():
            continue
            
        subfolder_name = subfolder.name
        print(f"\nProcessing subfolder: {subfolder_name}")
        
        try:
            # Get parameters for this specific subfolder
            if subfolder_name in subfolder_parameters:
                current_params = subfolder_parameters[subfolder_name].copy()
                for key, value in default_parameters.items():
                    if key not in current_params:
                        current_params[key] = value
                print(f"  Using custom parameters for {subfolder_name}")
            else:
                current_params = default_parameters.copy()
                print(f"  Using default parameters for {subfolder_name}")
            
            # Look for corresponding data folder in root directory
            data_folder = root_path / subfolder_name
            if not data_folder.exists():
                warning_msg = f"Warning: No corresponding data folder found for {subfolder_name}"
                print(warning_msg)
                processing_summary['skipped_subfolders'].append({
                    'name': subfolder_name,
                    'reason': 'No corresponding data folder'
                })
                continue
                
            # Process each shortened_* folder
            shortened_folders = glob.glob(str(data_folder / "shortened_*"))
            subfolder_success = True
            subfolder_experiments = 0
            subfolder_blobs = 0
            
            for shortened_folder in shortened_folders:
                shortened_path = Path(shortened_folder)
                shortened_name = shortened_path.name
                
                print(f"  Processing {shortened_name}")
                
                # Find corresponding shortened folder in segmentation_output
                seg_shortened_path = subfolder / shortened_name
                if not seg_shortened_path.exists():
                    warning_msg = f"No corresponding segmentation folder for {shortened_name}"
                    print(f"    Warning: {warning_msg}")
                    continue
                
                # Process each subsubfolder that exists in segmentation_output
                for subsubfolder in seg_shortened_path.iterdir():
                    if not subsubfolder.is_dir():
                        continue
                        
                    print(f"    Processing subsubfolder: {subsubfolder.name}")
                    
                    # Look for corresponding subsubfolder in the data location
                    data_subsubfolder = shortened_path / subsubfolder.name
                    if not data_subsubfolder.exists():
                        warning_msg = f"No corresponding data folder for {subsubfolder.name}"
                        print(f"      Warning: {warning_msg}")
                        processing_summary['failed_experiments'].append({
                            'name': f"{subfolder_name}/{shortened_name}/{subsubfolder.name}",
                            'reason': warning_msg
                        })
                        continue
                    
                    experiment_name = f"{subfolder_name}/{shortened_name}/{subsubfolder.name}"
                    
                    try:
                        # Look for raw folder in the DATA location
                        raw_folder = data_subsubfolder / "raw"
                        if not raw_folder.exists():
                            warning_msg = f"No 'raw' folder found in {subsubfolder.name}"
                            print(f"      {warning_msg}")
                            processing_summary['failed_experiments'].append({
                                'name': experiment_name,
                                'reason': warning_msg
                            })
                            continue
                        
                        # Output location is the current subsubfolder in segmentation_output
                        output_folder = subsubfolder
                        output_folder.mkdir(parents=True, exist_ok=True)
                        
                        # Get all image files from the DATA raw folder
                        image_extensions = ['*.tif', '*.tiff', '*.png', '*.jpg', '*.jpeg']
                        image_files = []
                        for ext in image_extensions:
                            image_files.extend(glob.glob(str(raw_folder / ext)))
                        
                        if not image_files:
                            warning_msg = f"No images found in {raw_folder}"
                            print(f"      {warning_msg}")
                            processing_summary['failed_experiments'].append({
                                'name': experiment_name,
                                'reason': warning_msg
                            })
                            continue
                        
                        image_files = sorted(image_files)
                        print(f"      Found {len(image_files)} images")
                        processing_summary['total_images_processed'] += len(image_files)
                        
                        # Process images in batches to prevent memory buildup
                        all_blob_data = []
                        
                        for i in range(0, len(image_files), max_images_per_batch):
                            batch_end = min(i + max_images_per_batch, len(image_files))
                            batch_files = image_files[i:batch_end]
                            
                            print(f"        Processing batch {i//max_images_per_batch + 1} "
                                  f"({len(batch_files)} images)")
                            
                            batch_blob_data = []
                            
                            for image_file in batch_files:
                                try:
                                    image_path = Path(image_file)
                                    timepoint = extract_timepoint_from_filename(image_path.name)
                                    
                                    # Detect blobs
                                    blob_data_list = detect_blobs_single_image(image_path, **current_params)
                                    
                                    if blob_data_list is not None:
                                        for blob_data in blob_data_list:
                                            complete_blob_data = [blob_data[0], blob_data[1], timepoint, 
                                                                 blob_data[2], blob_data[3], blob_data[4]]
                                            batch_blob_data.append(complete_blob_data)
                                except Exception as e:
                                    error_msg = f"Error processing image {image_file}: {str(e)}"
                                    print(f"          Warning: {error_msg}")
                                    processing_summary['errors'].append(error_msg)
                            
                            # Add batch data to overall collection
                            all_blob_data.extend(batch_blob_data)
                            
                            # Explicit cleanup after each batch
                            del batch_blob_data
                            gc.collect()
                            
                            print(f"        Batch complete. Total blobs so far: {len(all_blob_data)}")
                        
                        # Save blob data as NPY file
                        if all_blob_data:
                            blob_array = np.array(all_blob_data)
                            output_filename = f"blobs_{subsubfolder.name}.npy"
                            output_path = output_folder / output_filename
                            
                            np.save(output_path, blob_array)
                            print(f"      Saved {len(all_blob_data)} blobs to {output_path}")
                            print(f"      Array shape: {blob_array.shape}")
                            
                            processing_summary['successful_experiments'].append({
                                'name': experiment_name,
                                'images': len(image_files),
                                'blobs': len(all_blob_data),
                                'output_file': str(output_path)
                            })
                            processing_summary['total_blobs_detected'] += len(all_blob_data)
                            subfolder_experiments += 1
                            subfolder_blobs += len(all_blob_data)
                            
                            # Clean up large arrays
                            del blob_array, all_blob_data
                            gc.collect()
                        else:
                            warning_msg = f"No blobs detected in {subsubfolder.name}"
                            print(f"      {warning_msg}")
                            processing_summary['failed_experiments'].append({
                                'name': experiment_name,
                                'reason': warning_msg
                            })
                            
                    except Exception as e:
                        error_msg = f"Error processing experiment {experiment_name}: {str(e)}"
                        print(f"      Error: {error_msg}")
                        processing_summary['errors'].append(error_msg)
                        processing_summary['failed_experiments'].append({
                            'name': experiment_name,
                            'reason': f"Exception: {str(e)}"
                        })
                        subfolder_success = False
            
            # Record subfolder status
            if subfolder_success and subfolder_experiments > 0:
                processing_summary['successful_subfolders'].append({
                    'name': subfolder_name,
                    'experiments': subfolder_experiments,
                    'total_blobs': subfolder_blobs
                })
            elif subfolder_experiments == 0:
                processing_summary['skipped_subfolders'].append({
                    'name': subfolder_name,
                    'reason': 'No valid experiments found'
                })
            else:
                processing_summary['failed_subfolders'].append({
                    'name': subfolder_name,
                    'reason': 'Errors during processing'
                })
                
        except Exception as e:
            error_msg = f"Error processing subfolder {subfolder_name}: {str(e)}"
            print(f"  Error: {error_msg}")
            processing_summary['errors'].append(error_msg)
            processing_summary['failed_subfolders'].append({
                'name': subfolder_name,
                'reason': f"Exception: {str(e)}"
            })
    
    return processing_summary

# Main execution with memory monitoring
if __name__ == "__main__":
    import psutil
    import os
    
    # Print initial memory usage
    process = psutil.Process(os.getpid())
    print(f"Initial memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
    
    # Your existing configuration
    root_directory = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09"
    
    default_params = {
        'min_distance': 30,
        'clipLimit': 0.6,
        'tileGridSize': (16, 16),
        'dark_minThreshold': 0,
        'dark_maxThreshold': 125,
        'dark_minArea': 35,
        'dark_maxArea': 800,
        'bright_minThreshold': 90,
        'bright_maxThreshold': 255,
        'bright_minArea': 35,
        'bright_maxArea': 800
    }
    
    # Your complete subfolder_params from the latest code
    subfolder_params = {
        'Lead_1': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 80,
            'bright_maxThreshold': 255,
            'bright_minArea': 50,
            'bright_maxArea': 800
        },
        'Lead_2': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 30,
            'dark_maxArea': 800,
            'bright_minThreshold': 80,
            'bright_maxThreshold': 255,
            'bright_minArea': 50,
            'bright_maxArea': 800
        },
        'Lead_3': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 100,
            'bright_maxThreshold': 255,
            'bright_minArea': 50,
            'bright_maxArea': 800
        },
        'Lead_4': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 100,
            'bright_maxThreshold': 255,
            'bright_minArea': 50,
            'bright_maxArea': 800
        },
        'Zinc_3': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 90,
            'bright_maxThreshold': 255,
            'bright_minArea': 35,
            'bright_maxArea': 800
        },
        'Copper_3': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 15,
            'dark_maxArea': 800,
            'bright_minThreshold': 70,
            'bright_maxThreshold': 255,
            'bright_minArea': 25,
            'bright_maxArea': 800
        },
        'Copper_4': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 25,
            'dark_maxArea': 800,
            'bright_minThreshold': 70,
            'bright_maxThreshold': 255,
            'bright_minArea': 25,
            'bright_maxArea': 800
        },
        'Nickel_1': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 25,
            'dark_maxArea': 800,
            'bright_minThreshold': 65,
            'bright_maxThreshold': 255,
            'bright_minArea': 25,
            'bright_maxArea': 800
        },
        'Nickel_3': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 25,
            'dark_maxArea': 800,
            'bright_minThreshold': 65,
            'bright_maxThreshold': 255,
            'bright_minArea': 25,
            'bright_maxArea': 800
        },
        'Nickel_4': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 25,
            'dark_maxArea': 800,
            'bright_minThreshold': 85,
            'bright_maxThreshold': 255,
            'bright_minArea': 25,
            'bright_maxArea': 800
        }
    }
    
    print(f"Starting memory-optimized batch blob detection...")
    print(f"Processing images in batches of 50 to prevent memory issues")
    
    try:
        summary = process_batch_blob_detection(
            root_directory=root_directory,
            subfolder_parameters=subfolder_params,
            default_parameters=default_params,
            max_images_per_batch=50  # Process 50 images at a time
        )
        
        # Print comprehensive summary
        print("\n" + "="*80)
        print("BATCH PROCESSING COMPLETE - SUMMARY REPORT")
        print("="*80)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"Final memory usage: {final_memory:.1f} MB")
        
        # Overall statistics
        print(f"\nOVERALL STATISTICS:")
        print(f"Total images processed: {summary['total_images_processed']}")
        print(f"Total blobs detected: {summary['total_blobs_detected']}")
        print(f"Successful experiments: {len(summary['successful_experiments'])}")
        print(f"Failed experiments: {len(summary['failed_experiments'])}")
        print(f"Successful subfolders: {len(summary['successful_subfolders'])}")
        print(f"Failed subfolders: {len(summary['failed_subfolders'])}")
        print(f"Skipped subfolders: {len(summary['skipped_subfolders'])}")
        
        # Successful subfolders details
        if summary['successful_subfolders']:
            print(f"\nSUCCESSFUL SUBFOLDERS ({len(summary['successful_subfolders'])}):")
            for sf in summary['successful_subfolders']:
                print(f"    {sf['name']}: {sf['experiments']} experiments, {sf['total_blobs']} total blobs")
        
        # Failed operations details
        success_rate = len(summary['successful_experiments']) / (len(summary['successful_experiments']) + len(summary['failed_experiments'])) * 100 if (len(summary['successful_experiments']) + len(summary['failed_experiments'])) > 0 else 0
        
        if summary['failed_subfolders'] or summary['failed_experiments'] or summary['errors']:
            print(f"\n   ISSUES DETECTED (Success rate: {success_rate:.1f}%):")
            
            if summary['failed_subfolders']:
                print(f"\nFAILED SUBFOLDERS ({len(summary['failed_subfolders'])}):")
                for sf in summary['failed_subfolders']:
                    print(f"    {sf['name']}: {sf['reason']}")
            
            if summary['skipped_subfolders']:
                print(f"\nSKIPPED SUBFOLDERS ({len(summary['skipped_subfolders'])}):")
                for sf in summary['skipped_subfolders']:
                    print(f"    {sf['name']}: {sf['reason']}")
            
            if summary['failed_experiments']:
                print(f"\nFAILED EXPERIMENTS ({len(summary['failed_experiments'])}):")
                for exp in summary['failed_experiments'][:10]:  # Show first 10
                    print(f"    {exp['name']}: {exp['reason']}")
                if len(summary['failed_experiments']) > 10:
                    print(f"  ... and {len(summary['failed_experiments']) - 10} more")
            
            if summary['errors']:
                print(f"\nERRORS ENCOUNTERED ({len(summary['errors'])}):")
                for error in summary['errors'][:5]:  # Show first 5
                    print(f"     {error}")
                if len(summary['errors']) > 5:
                    print(f"  ... and {len(summary['errors']) - 5} more errors")
        else:
            print(f"\n  ALL OPERATIONS SUCCESSFUL! (Success rate: 100%)")
        
        # Recommendations
        if summary['failed_experiments'] or summary['errors']:
            print(f"\nRECOMMENDations:")
            if any('No images found' in str(exp.get('reason', '')) for exp in summary['failed_experiments']):
                print("  - Some experiments had no images - check directory structure")
            if any('No \'raw\' folder' in str(exp.get('reason', '')) for exp in summary['failed_experiments']):
                print("  - Some experiments missing 'raw' folders - verify folder naming")
            if summary['errors']:
                print("  - Errors occurred during processing - consider reducing batch size")
                print("    Try: max_images_per_batch=25 or max_images_per_batch=10")
        
        print("="*80)
        
    except Exception as e:
        print(f"Critical error during processing: {e}")
        current_memory = process.memory_info().rss / 1024 / 1024
        print(f"Memory usage at error: {current_memory:.1f} MB")