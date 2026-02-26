import numpy as np
import pytest
from converter.calulation import (
    expand_array_with_nan,
    theta_lambda_to_q,
    q_with_resolution_from_slits
)
from converter.datatypes import SlitData


class TestExpandArrayWithNan:
    def test_expand_array_basic(self):
        arr = np.array([1, 2, 3])
        new_shape = (5,)
        result = expand_array_with_nan(arr, new_shape)
        expected = np.array([1, 2, 3, np.nan, np.nan])
        np.testing.assert_array_equal(result, expected)

    def test_expand_array_2d(self):
        arr = np.array([[1, 2], [3, 4]])
        new_shape = (3, 4)
        result = expand_array_with_nan(arr, new_shape)
        expected = np.array([
            [1, 2, np.nan, np.nan],
            [3, 4, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan]
        ])
        np.testing.assert_array_equal(result, expected)

    def test_expand_array_same_shape(self):
        arr = np.array([1, 2, 3])
        new_shape = (3,)
        result = expand_array_with_nan(arr, new_shape)
        np.testing.assert_array_equal(result, arr)

    def test_expand_array_smaller_shape_raises(self):
        arr = np.array([1, 2, 3, 4, 5])
        new_shape = (3,)
        with pytest.raises(ValueError, match="New shape must be greater than or equal"):
            expand_array_with_nan(arr, new_shape)

    def test_expand_array_from_list(self):
        arr = [1, 2, 3]
        new_shape = (5,)
        result = expand_array_with_nan(arr, new_shape)
        expected = np.array([1, 2, 3, np.nan, np.nan])
        np.testing.assert_array_equal(result, expected)


class TestThetaLambdaToQ:
    def test_theta_lambda_to_q_single_value_degrees(self):
        theta = 1.0
        lamda = 5.0
        q = theta_lambda_to_q(theta, lamda, degrees=True)
        expected_q = (4 * np.pi / lamda) * np.sin(np.radians(theta))
        np.testing.assert_allclose(q, expected_q)

    def test_theta_lambda_to_q_array_degrees(self):
        theta = np.array([0.5, 1.0, 2.0])
        lamda = 5.0
        q = theta_lambda_to_q(theta, lamda, degrees=True)
        expected_q = (4 * np.pi / lamda) * np.sin(np.radians(theta))
        np.testing.assert_allclose(q, expected_q)

    def test_theta_lambda_to_q_radians(self):
        theta = np.array([0.01, 0.02, 0.03])
        lamda = 5.0
        q = theta_lambda_to_q(theta, lamda, degrees=False)
        expected_q = (4 * np.pi / lamda) * np.sin(theta)
        np.testing.assert_allclose(q, expected_q)

    def test_theta_lambda_to_q_single_value_radians(self):
        theta = 0.02
        lamda = 5.0
        q = theta_lambda_to_q(theta, lamda, degrees=False)
        expected_q = (4 * np.pi / lamda) * np.sin(theta)
        np.testing.assert_allclose(q, expected_q)

    def test_theta_lambda_to_q_array_lamda(self):
        theta = 1.0
        lamda = np.array([4.0, 5.0, 6.0])
        q = theta_lambda_to_q(theta, lamda, degrees=True)
        expected_q = (4 * np.pi / lamda) * np.sin(np.radians(theta))
        np.testing.assert_allclose(q, expected_q)


class TestQWithResolutionFromSlits:
    def test_q_with_resolution_basic(self):
        theta_deg = np.array([0.5, 1.0, 2.0])
        lamda = 5.0
        slits_data = SlitData(
            slit1_width=1.0,
            slit2_width=1.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        dlam_rel = 0.01

        q, dq = q_with_resolution_from_slits(theta_deg, lamda, slits_data, dlam_rel)

        assert q.shape == theta_deg.shape
        assert dq.shape == theta_deg.shape
        assert np.all(dq > 0)

    def test_q_with_resolution_single_value(self):
        theta_deg = 1.0
        lamda = 5.0
        slits_data = SlitData(
            slit1_width=1.0,
            slit2_width=1.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        dlam_rel = 0.01

        q, dq = q_with_resolution_from_slits(theta_deg, lamda, slits_data, dlam_rel)

        assert np.isscalar(q) or q.shape == ()
        assert np.isscalar(dq) or dq.shape == ()

    def test_q_with_resolution_slits_reversed(self):
        theta_deg = np.array([1.0])
        lamda = 5.0
        slits_data = SlitData(
            slit1_width=1.0,
            slit2_width=1.0,
            slit1_position=1000.0,
            slit2_position=0.0,
            units='mm'
        )
        dlam_rel = 0.01

        q, dq = q_with_resolution_from_slits(theta_deg, lamda, slits_data, dlam_rel)

        assert q.shape == theta_deg.shape

    def test_q_with_resolution_zero_dlam(self):
        theta_deg = np.array([1.0])
        lamda = 5.0
        slits_data = SlitData(
            slit1_width=1.0,
            slit2_width=1.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        dlam_rel = 0.0

        q, dq = q_with_resolution_from_slits(theta_deg, lamda, slits_data, dlam_rel)

        assert np.all(dq > 0)

    def test_q_with_resolution_large_theta(self):
        theta_deg = np.array([45.0])
        lamda = 5.0
        slits_data = SlitData(
            slit1_width=1.0,
            slit2_width=1.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        dlam_rel = 0.01

        q, dq = q_with_resolution_from_slits(theta_deg, lamda, slits_data, dlam_rel)

        assert q.shape == theta_deg.shape
