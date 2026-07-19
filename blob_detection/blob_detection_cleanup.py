"""
Cleanup script for segmentation_output directory
Removes subsubfolders that only contain blobs_*.npy files and no other content

PURPOSE:
This script cleans up unnecessary subsubfolders created in segmentation_output
that contain only NPY blob files but no other data (like PNG images or raw data).
These empty folders would cause the blob detection script to skip corresponding
data folders that actually need processing.

SAFETY FEATURES:
- Shows what will be deleted before doing anything
- Only deletes folders that match specific criteria
- Preserves folders with any non-NPY content

"""

import shutil
from pathlib import Path


def scan_for_cleanup_candidates(segmentation_output_path):
    """
    Scan segmentation_output directory for subsubfolders that should be deleted
    Returns list of folders that only contain blobs_*.npy files
    """
    cleanup_candidates = []

    seg_path = Path(segmentation_output_path)

    if not seg_path.exists():
        print(f"Error: Segmentation output path does not exist: {segmentation_output_path}")
        return cleanup_candidates

    # Walk through all subsubfolders: segmentation_output/subfolder/shortened/subsubfolder
    for subfolder in seg_path.iterdir():
        if not subfolder.is_dir():
            continue

        for shortened_folder in subfolder.iterdir():
            if not shortened_folder.is_dir():
                continue

            for subsubfolder in shortened_folder.iterdir():
                if not subsubfolder.is_dir():
                    continue

                # Check contents of this subsubfolder
                all_files = list(subsubfolder.glob('*'))

                if not all_files:
                    # Empty folder - candidate for deletion
                    cleanup_candidates.append({
                        'path': subsubfolder,
                        'reason': 'Empty folder',
                        'relative_path': str(subsubfolder.relative_to(seg_path))
                    })
                else:
                    # Check if it only contains blobs_*.npy files
                    npy_files = list(subsubfolder.glob('blobs_*.npy'))
                    other_files = [f for f in all_files if
                                   not f.name.startswith('blobs_') or not f.name.endswith('.npy')]

                    if npy_files and not other_files:
                        # Only contains blobs NPY files - candidate for deletion
                        cleanup_candidates.append({
                            'path': subsubfolder,
                            'reason': f'Only contains {len(npy_files)} blobs_*.npy file(s)',
                            'relative_path': str(subsubfolder.relative_to(seg_path))
                        })

    return cleanup_candidates


def preview_cleanup(candidates):
    """Show what will be deleted"""
    if not candidates:
        print("No cleanup candidates found - segmentation_output is already clean!")
        return False

    print(f"\nFound {len(candidates)} folders that can be cleaned up:")
    print("-" * 80)

    for candidate in candidates:
        print(f"DELETE: {candidate['relative_path']}")
        print(f"  Reason: {candidate['reason']}")

    print("-" * 80)
    print(f"Total folders to delete: {len(candidates)}")
    return True


def perform_cleanup(candidates):
    """Actually delete the folders"""
    deleted_count = 0
    errors = []

    for candidate in candidates:
        try:
            shutil.rmtree(candidate['path'])
            print(f"Deleted: {candidate['relative_path']}")
            deleted_count += 1
        except Exception as e:
            error_msg = f"Failed to delete {candidate['relative_path']}: {str(e)}"
            print(f"ERROR: {error_msg}")
            errors.append(error_msg)

    print(f"\nCleanup complete!")
    print(f"Successfully deleted: {deleted_count} folders")
    if errors:
        print(f"Errors encountered: {len(errors)}")
        for error in errors:
            print(f"  - {error}")

    return deleted_count, errors


def main():
    # HARD-CODED SEGMENTATION OUTPUT PATH - MODIFY THIS
    segmentation_output_path = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09/segmentation_output"

    print("Segmentation Output Cleanup Script")
    print("=" * 50)
    print(f"Target directory: {segmentation_output_path}")
    print()
    print("This script will remove subsubfolders that:")
    print("  1. Are empty, OR")
    print("  2. Only contain blobs_*.npy files (no other content)")
    print()

    # Scan for cleanup candidates
    print("Scanning for cleanup candidates...")
    candidates = scan_for_cleanup_candidates(segmentation_output_path)

    # Preview what will be deleted
    has_candidates = preview_cleanup(candidates)

    if not has_candidates:
        return

    # Automatically proceed with cleanup (no user input required)
    print("\nProceeding with cleanup automatically...")
    deleted_count, errors = perform_cleanup(candidates)

    if deleted_count > 0:
        print(f"\nSUCCESS: Cleaned up {deleted_count} unnecessary folders.")
        print("Your segmentation_output directory is now ready for blob detection.")


if __name__ == "__main__":
    main()
