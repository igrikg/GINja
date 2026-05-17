import numpy as np
from numpy.typing import NDArray

from converter.datatypes import SlitData


def footprint_correction_two_slits(angles_deg: NDArray, slits_data: SlitData, sample_length: float) -> NDArray:
    """
    Get footprint correction factor using two-slit geometry.

    The center of the beam has constant intensity, in the outside the intensity decreases linearly until.
    Parameters:
        angles_deg (np.ndarray): Incident angles in degrees.
        slits_data (SlitData): Slits parameters in mm.
        sample_length (float): Sample length (mm).
    Returns:
        np.ndarray: Correction factor data.
    """
    theta = np.radians(angles_deg)
    s1w = slits_data.slit1_width
    s2w = slits_data.slit2_width
    l1 = np.abs(slits_data.slit1_position)
    l2 = np.abs(slits_data.slit2_position)
    beam_center = s2w - (s1w - s2w) * l2 / (l1+l2)
    beam_size = (s1w + s2w) * (l1 + l2) / (l1 - l2) - s1w

    if sample_length <= 0:
        return np.ones_like(theta)

    arg2 = np.clip(beam_center / sample_length, -1.0, 1.0)
    theta2 = np.arcsin(arg2)
    arg3 = np.clip(beam_size / sample_length, -1.0, 1.0)
    theta3 = np.arcsin(arg3)

    full_beam = beam_center + (beam_size - beam_center) / 2.0
    scale_outer = np.where(full_beam == 0, 0, (beam_size - beam_center) / 2.0 / full_beam)
    
    denom = (theta3 - theta2) ** 2
    denom = np.where(denom == 0, 1e-10, denom)

    correction_factor = np.where(
        theta < theta3,
        np.where(
            theta < theta2,
            (1.0 - scale_outer) * theta / np.where(theta2 == 0, 1e-10, theta2),
            (1.0 - scale_outer) + (1.0 - (theta - theta3) ** 2 / denom) * scale_outer,
        ),
        1.0,
    )
    return 1 / correction_factor


def absorption_correction(theta, lamda, mu, sample):
    """
    Get absorption correction coefficients.

    Parameters:
        lamda (float): Wavelength in angstroms.
        theta (np.ndarray): Incident angles in degrees.
        mu (float): Linear absorption coefficient (in 1/mm/angstrom or matching units).
        sample (SampleData): Object with `length` and `thickness` attributes (in mm units).

    Returns:
        np.ndarray: Correction factor data.
    """
    theta = np.radians(theta)
    # Critical angle where beam crosses entire sample length
    theta1 = np.arctan((sample.thickness / sample.length) * 2)
    sin_theta = np.clip(np.sin(theta), 1e-6, None)
    cos_theta = np.clip(np.cos(theta), 1e-6, None)
    # Calculate path length through sample
    x = np.where(
        theta < theta1,
        sample.length / cos_theta,                # Grazing incidence
        2 * sample.thickness / sin_theta         # Deep penetration
    )
    corr = np.exp(-mu * lamda * x)

    return corr
