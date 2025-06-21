import numpy as np

from .datatypes import SlitData


def expand_array_with_nan(arr, new_shape):
    """
    Expands a NumPy array to the specified new shape,
    filling new elements with np.nan.

    Parameters:
        arr (np.ndarray): Original NumPy array.
        new_shape (tuple): Desired new shape (must be >= arr.shape in all dimensions).

    Returns:
        np.ndarray: New array with expanded shape filled with np.nan.
    """
    arr = np.asarray(arr)
    if any(n < o for n, o in zip(new_shape, arr.shape)):
        raise ValueError("New shape must be greater than or equal to original shape in all dimensions.")

    # Create a new array filled with NaN
    result = np.full(new_shape, np.nan, dtype=float)

    # Generate slices to copy data
    slices = tuple(slice(0, s) for s in arr.shape)
    result[slices] = arr

    return result


def theta_lambda_to_q(theta, lamda, degrees=True):
    """
    Convert angle (theta) and wavelength (lambda) to momentum transfer q.

    Parameters:
        theta (np.ndarray or float): Incident angle(s), in degrees or radians.
        lamda (float or np.ndarray): Wavelength(s) in Ångströms.
        degrees (bool): If True, theta is in degrees. If False, in radians.

    Returns:
        np.ndarray or float: q values in Å⁻¹.
    """
    if degrees:
        theta = np.radians(theta)

    q = (4 * np.pi / lamda) * np.sin(theta)
    return q


def q_with_resolution_from_slits(theta_deg, lamda, slits_data: SlitData, dlam_rel):
    """
    Calculate q and dq using slit-defined angular divergence and known dλ/λ.

    Parameters:
        theta_deg (array-like): Incident angles in degrees.
        lamda (float): Wavelength in Ångströms.
        slits_data (SlitData): Slits parameters in mm.
        dlam_rel (float): Relative wavelength spread Δλ/λ.

    Returns:
        q (np.ndarray): Momentum transfer in Å⁻¹.
        dq (np.ndarray): Resolution Δq in Å⁻¹.
    """
    S1 = slits_data.slit1_width
    S2 = slits_data.slit2_width
    L12 = np.abs(slits_data.slit1_position - slits_data.slit2_position)

    theta_rad = np.radians(theta_deg)
    q = (4 * np.pi / lamda) * np.sin(theta_rad)

    # Angular divergence Δθ (radians)
    dtheta = (S1 + S2) / (2 * L12)

    # Relative angular resolution
    rel_dtheta = dtheta / np.tan(theta_rad)

    # Total relative q-resolution
    rel_dq = np.sqrt(dlam_rel**2 + rel_dtheta**2)
    dq = q * rel_dq

    return q, dq









