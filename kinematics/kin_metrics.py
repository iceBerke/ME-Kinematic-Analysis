# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# Pure per-track kinematic metric computation. NO file I/O, NO folder traversal.
#
# This module holds the "science" of stage 7 of the pipeline, extracted from
# final_kin_param_extraction_v3/v4 so that a single track can be analysed in
# isolation (e.g. from a REPL or notebook) without walking the whole data tree:
#
#     import numpy as np
#     from kin_metrics import compute_track_metrics
#     x, y, t = np.load("aligned_blobs_t3_converted.npy")[:, :3].T
#     compute_track_metrics(x, y, t)
#
# Input coordinates are expected in micrometers and times in seconds, i.e. the
# output of alignment_*/time_coordinates_conversions_* (stage 6).
#
import math

import numpy as np
from scipy.ndimage import uniform_filter1d  # For applying a moving average (smoothing)

# Default analysis parameters. Pass a dict with any subset of these keys to
# compute_track_metrics() to override them; anything omitted falls back here.
DEFAULT_PARAMS = {
    # Threshold for significant direction change (in degrees)
    "ANGLE_THRESHOLD": 30,

    # Minimum displacement to consider (to filter out noise)
    "MIN_DISPLACEMENT": 0.01,  # Adjust based on your data scale

    # Minimum time allowed between subsequent direction changes (in seconds)
    "MIN_TIME_BETWEEN_DIRECTION_CHANGES": 0.1,

    # Maximum speed to consider (in µm/s)
    "MAX_SPEED": 60,  # µm/s

    # Smoothing window size (for the moving average filter)
    "SMOOTHING_WINDOW": 1,  # Window = 1 means NO SMOOTHING - preserves all original position data
                            # This maintains all genuine biological movements (including sharp turns)
                            # but also keeps any tracking noise/jitter in the data
}


def calculate_angle(v1, v2):
    """Angle between two 2D vectors, in degrees. NaN if either has zero length."""
    dot_prod = np.dot(v1, v2)
    mag1 = np.linalg.norm(v1)
    mag2 = np.linalg.norm(v2)
    if mag1 == 0 or mag2 == 0:
        return np.nan
    cos_theta = dot_prod / (mag1 * mag2)
    cos_theta = max(min(cos_theta, 1), -1)  # Clamp cos_theta to avoid NaNs due to floating point errors
    angle = math.acos(cos_theta)
    return np.degrees(angle)


def smooth_data(data, window_size):
    """Smooth data using a moving average filter."""
    return uniform_filter1d(data, size=window_size)


def resolve_params(params=None):
    """Merge user-supplied parameters over DEFAULT_PARAMS."""
    resolved = dict(DEFAULT_PARAMS)
    if params:
        resolved.update(params)
    return resolved


def compute_track_metrics(x, y, t, params=None):
    """
    Compute motion metrics for a single track.

    Arguments:
        x, y : positions in micrometers (1D arrays of equal length)
        t    : timepoints in seconds (1D array of equal length)
        params : optional dict overriding DEFAULT_PARAMS

    Returns a dict. If the track cannot be analysed the dict contains only
    {'skip_reason': <str>}; callers should test that key first. On success
    'skip_reason' is None and the dict holds:

        mean_velocity          mean of the speed-filtered instantaneous velocities (µm/s)
        std_velocity           population std of those velocities (µm/s)
        speed_dynamic          std/mean as a percentage (NaN if mean is 0)
        straightness_index     net displacement / path length (NaN if path length is 0)
        direction_change_rate  significant direction changes per second (NaN if total_time is 0)
        total_time             t[-1] - t[0] (s)
        num_direction_changes  count of significant direction changes
        direction_change_timepoints  list of t values at which they occurred (s)
        num_velocities         instantaneous velocities before the speed filter
        num_velocities_removed how many the MAX_SPEED filter discarded

    Note: straightness uses the smoothed first/last positions for net displacement
    but sums only the speed-filtered step displacements for path length; direction
    changes are evaluated on all steps, including those the speed filter removed.
    This matches the original v3/v4 behaviour exactly.
    """
    p = resolve_params(params)

    x = np.asarray(x)
    y = np.asarray(y)
    t = np.asarray(t)

    if len(x) < 2:
        return {"skip_reason": "track too short"}

    # Apply smoothing to x and y coordinates
    x_smooth = smooth_data(x, p["SMOOTHING_WINDOW"])
    y_smooth = smooth_data(y, p["SMOOTHING_WINDOW"])

    # Calculate displacements and time differences
    dx = np.diff(x_smooth)
    dy = np.diff(y_smooth)
    dt = np.diff(t)

    # Calculate instantaneous velocities
    displacements = np.sqrt(dx ** 2 + dy ** 2)

    # Avoid division by zero
    valid_dt_mask = dt > 0
    if not np.any(valid_dt_mask):
        return {"skip_reason": "invalid time differences"}

    velocities = np.divide(displacements, dt, out=np.zeros_like(displacements), where=valid_dt_mask)

    # Apply speed filter
    valid_speeds_mask = (velocities <= p["MAX_SPEED"]) & valid_dt_mask
    filtered_velocities = velocities[valid_speeds_mask]
    filtered_displacements = displacements[valid_speeds_mask]

    # Skip if no valid speeds are left after filtering
    if len(filtered_velocities) == 0:
        return {"skip_reason": "no valid velocities after filtering"}

    # Calculate mean and standard deviation of filtered velocities
    mean_velocity = np.mean(filtered_velocities)
    std_velocity = np.std(filtered_velocities)

    # Calculate speed dynamic (stdv as a percentage of mean speed)
    speed_dynamic = (std_velocity / mean_velocity) * 100 if mean_velocity != 0 else np.nan

    # Calculate net displacement and path length
    net_displacement = np.sqrt((x_smooth[-1] - x_smooth[0]) ** 2 + (y_smooth[-1] - y_smooth[0]) ** 2)
    path_length = np.sum(filtered_displacements)
    straightness_index = net_displacement / path_length if path_length != 0 else np.nan

    # Calculate turning angles and store timepoints of significant direction changes
    direction_changes = 0
    significant_timepoints = []
    last_direction_change_time = None

    for i in range(1, len(dx)):
        v1 = np.array([dx[i - 1], dy[i - 1]])
        v2 = np.array([dx[i], dy[i]])

        if np.linalg.norm(v1) < p["MIN_DISPLACEMENT"] or np.linalg.norm(v2) < p["MIN_DISPLACEMENT"]:
            continue

        angle = calculate_angle(v1, v2)
        if not np.isnan(angle) and angle > p["ANGLE_THRESHOLD"]:
            if last_direction_change_time is None:
                direction_changes += 1
                significant_timepoints.append(t[i])
                last_direction_change_time = t[i]
            else:
                if t[i] - last_direction_change_time >= p["MIN_TIME_BETWEEN_DIRECTION_CHANGES"]:
                    direction_changes += 1
                    significant_timepoints.append(t[i])
                    last_direction_change_time = t[i]

    total_time = t[-1] - t[0]
    direction_change_rate = direction_changes / total_time if total_time > 0 else np.nan

    result = {
        "skip_reason": None,
        "mean_velocity": mean_velocity,
        "std_velocity": std_velocity,
        "speed_dynamic": speed_dynamic,
        "straightness_index": straightness_index,
        "direction_change_rate": direction_change_rate,
        "total_time": total_time,
        "num_direction_changes": direction_changes,
        "direction_change_timepoints": significant_timepoints,
        "num_velocities": len(velocities),
        "num_velocities_removed": len(velocities) - len(filtered_velocities),
    }

    # Clear large intermediates promptly (these scripts run over very large datasets)
    del x_smooth, y_smooth, dx, dy, dt, displacements, velocities
    del filtered_velocities, filtered_displacements

    return result
