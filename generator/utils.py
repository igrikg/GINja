import numpy as np


def ideal_reflectivity(m, scale, alpha, m_max):
    out = scale * np.where(m < 1.0, 1.0, np.where(m <= m_max, 1.0 - (m - 1.0) * alpha, 0.0))
    return out