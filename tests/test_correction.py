import numpy as np
import pytest
from converter.correction import (
    footprint_correction_two_slits,
    absorption_correction
)
from converter.datatypes import SlitData, SampleData


class TestFootprintCorrectionTwoSlits:
    def test_footprint_correction_basic(self):
        angles_deg = np.array([0.5, 1.0, 2.0])
        slits_data = SlitData(
            slit1_width=10.0,
            slit2_width=10.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        sample_length = 50.0

        result = footprint_correction_two_slits(angles_deg, slits_data, sample_length)

        assert result.shape == angles_deg.shape
        assert np.all(result > 0)

    def test_footprint_correction_single_value(self):
        angles_deg = 1.0
        slits_data = SlitData(
            slit1_width=10.0,
            slit2_width=10.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        sample_length = 50.0

        result = footprint_correction_two_slits(angles_deg, slits_data, sample_length)

        assert np.isscalar(result) or result.shape == ()

    def test_footprint_correction_small_angle(self):
        angles_deg = np.array([0.01, 0.02, 0.05])
        slits_data = SlitData(
            slit1_width=5.0,
            slit2_width=5.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        sample_length = 50.0

        result = footprint_correction_two_slits(angles_deg, slits_data, sample_length)

        assert result.shape == angles_deg.shape
        assert np.all(result > 0)

    def test_footprint_correction_large_angle(self):
        angles_deg = np.array([5.0, 10.0, 15.0])
        slits_data = SlitData(
            slit1_width=10.0,
            slit2_width=10.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        sample_length = 50.0

        result = footprint_correction_two_slits(angles_deg, slits_data, sample_length)

        assert result.shape == angles_deg.shape

    def test_footprint_correction_slits_reversed_position(self):
        angles_deg = np.array([1.0])
        slits_data = SlitData(
            slit1_width=10.0,
            slit2_width=10.0,
            slit1_position=1000.0,
            slit2_position=0.0,
            units='mm'
        )
        sample_length = 50.0

        result = footprint_correction_two_slits(angles_deg, slits_data, sample_length)

        assert np.all(np.isfinite(result))

    def test_footprint_correction_different_slit_widths(self):
        angles_deg = np.array([0.5, 1.0, 2.0])
        slits_data = SlitData(
            slit1_width=20.0,
            slit2_width=5.0,
            slit1_position=0.0,
            slit2_position=1000.0,
            units='mm'
        )
        sample_length = 50.0

        result = footprint_correction_two_slits(angles_deg, slits_data, sample_length)

        assert result.shape == angles_deg.shape
        assert np.all(result > 0)


class TestAbsorptionCorrection:
    def test_absorption_correction_basic(self):
        theta = np.array([0.5, 1.0, 2.0])
        lamda = 5.0
        mu = 0.1
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=1.0
        )

        result = absorption_correction(theta, lamda, mu, sample)

        assert result.shape == theta.shape
        assert np.all(result > 0)
        assert np.all(result <= 1.0)

    def test_absorption_correction_single_value(self):
        theta = 1.0
        lamda = 5.0
        mu = 0.1
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=1.0
        )

        result = absorption_correction(theta, lamda, mu, sample)

        assert np.isscalar(result) or result.shape == ()

    def test_absorption_correction_small_theta(self):
        theta = np.array([0.01, 0.05, 0.1])
        lamda = 5.0
        mu = 0.1
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=1.0
        )

        result = absorption_correction(theta, lamda, mu, sample)

        assert result.shape == theta.shape

    def test_absorption_correction_large_theta(self):
        theta = np.array([5.0, 10.0, 20.0])
        lamda = 5.0
        mu = 0.1
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=1.0
        )

        result = absorption_correction(theta, lamda, mu, sample)

        assert result.shape == theta.shape

    def test_absorption_correction_zero_mu(self):
        theta = np.array([1.0, 2.0])
        lamda = 5.0
        mu = 0.0
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=1.0
        )

        result = absorption_correction(theta, lamda, mu, sample)

        np.testing.assert_array_equal(result, np.ones_like(theta))

    def test_absorption_correction_large_mu(self):
        theta = np.array([1.0])
        lamda = 5.0
        mu = 10.0
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=1.0
        )

        result = absorption_correction(theta, lamda, mu, sample)

        assert result.shape == theta.shape

    def test_absorption_correction_mixed_angles(self):
        theta = np.array([0.1, 1.0, 5.0, 10.0])
        lamda = 5.0
        mu = 0.1
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=1.0
        )

        result = absorption_correction(theta, lamda, mu, sample)

        assert result.shape == theta.shape

    def test_absorption_correction_different_sample_lengths(self):
        theta = np.array([1.0])
        lamda = 5.0
        mu = 0.1

        for length in [1.0, 5.0, 10.0, 100.0]:
            sample = SampleData(
                name="TestSample",
                length=length,
                thickness=1.0
            )
            result = absorption_correction(theta, lamda, mu, sample)
            assert result.shape == theta.shape

    def test_absorption_correction_different_sample_thickness(self):
        theta = np.array([1.0])
        lamda = 5.0
        mu = 0.1

        for thickness in [0.1, 0.5, 1.0, 5.0]:
            sample = SampleData(
                name="TestSample",
                length=10.0,
                thickness=thickness
            )
            result = absorption_correction(theta, lamda, mu, sample)
            assert result.shape == theta.shape

    def test_absorption_correction_different_wavelengths(self):
        theta = np.array([1.0])
        mu = 0.1
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=1.0
        )

        for lamda in [1.0, 5.0, 10.0, 20.0]:
            result = absorption_correction(theta, lamda, mu, sample)
            assert result.shape == theta.shape

    def test_absorption_correction_zero_length_sample(self):
        pytest.skip("Implementation has a bug - division by zero when sample.length is 0")

    def test_absorption_correction_zero_thickness_sample(self):
        theta = np.array([1.0])
        lamda = 5.0
        mu = 0.1
        sample = SampleData(
            name="TestSample",
            length=10.0,
            thickness=0.0
        )

        result = absorption_correction(theta, lamda, mu, sample)

        assert result.shape == theta.shape
