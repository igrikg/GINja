
import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock
from converter.reduction import DataReduction, BackgroundTypeCorrection
from converter.datatypes import AdsorptionTypeCorrection, IntensityTypeCorrection, DataSetOutput

# Mocking the complex data types and their dependencies
class MockDataSetMetadata:
    def __init__(self, owner, experiment, sample):
        self.owner = owner
        self.experiment = experiment
        self.sample = sample

class MockSample:
    def __init__(self, length=1.0, thickness=0.0, height=0.0):
        self.length = length
        self.thickness = thickness
        self.height = height

class MockSlitConfiguration:
    def __init__(self):
        self.slit1_width = 0.1
        self.slit2_width = 0.1
        self.slit1_position = 0
        self.slit2_position = 100

class MockInstrumentSettings:
    def __init__(self, slit_configuration=None, wavelength=1.0):
        self.slit_configuration = slit_configuration if slit_configuration is not None else MockSlitConfiguration()
        self.wavelength = wavelength

class MockMeasurement:
    def __init__(self, instrument_settings=None):
        self.instrument_settings = instrument_settings if instrument_settings is not None else MockInstrumentSettings()

class MockDataSource:
    def __init__(self, detector="2Ddata", region=(0, 1, 0, 1)):
        self.detector = detector
        self.region = region

class MockBackground:
    def __init__(self, use_correction=False, correction_type=BackgroundTypeCorrection.constValue, region=(0, 1, 0, 1), value=0):
        self.use_correction = use_correction
        self.correction_type = correction_type
        self.region = region
        self.value = value

class MockReduction:
    def __init__(self, foot_print_correction=False, absorption_correction=False, polarisation_correction=False, mu_type=AdsorptionTypeCorrection.constValue, mu_value=0, mu_enum=None):
        self.foot_print_correction = foot_print_correction
        self.absorption_correction = absorption_correction
        self.polarisation_correction = polarisation_correction
        self.mu_type = mu_type
        self.mu_value = mu_value
        self.mu_enum = mu_enum

class MockNormalisation:
    def __init__(self, monitor=False, time=False, intensity_norm=False, intensity_norm_type=IntensityTypeCorrection.constValue, intensity_value=1.0):
        self.monitor = monitor
        self.time = time
        self.intensity_norm = intensity_norm
        self.intensity_norm_type = intensity_norm_type
        self.intensity_value = intensity_value

class MockCorrectionParameters:
    def __init__(self, data_source=None, background=None, reduction=None, normalisation=None):
        self.data_source = data_source if data_source is not None else MockDataSource()
        self.background = background if background is not None else MockBackground()
        self.reduction = reduction if reduction is not None else MockReduction()
        self.normalisation = normalisation if normalisation is not None else MockNormalisation()

class MockMetadata:
    def __init__(self, file_path="test_file.nxs", owner="test_owner", experiment="test_experiment", sample="test_sample", polarisation=None):
        self.file_path = file_path
        self.owner = owner
        self.experiment = experiment
        self.sample = MockDataSetMetadata(owner, experiment, sample)
        self.polarisation = polarisation if polarisation is not None else ["up"]

    def get_dataset(self, name, polarisation):
        if name == 'theta':
            return np.array([0.1, 0.2, 0.3])
        if name == "2Ddata" or name == "detector_data":
            return np.ones((3, 2, 2)) * 10
        return np.array([1, 2, 3])

    def get_dataset_monitor(self, polarisation):
        return np.array([100, 100, 100])

    def get_dataset_time(self, polarisation):
        return np.array([1, 1, 1])

    def measurement(self, polarisation):
        return MockMeasurement()


def test_data_reduction_init():
    mock_metadata = MockMetadata()
    mock_parameters = MockCorrectionParameters()
    reduction = DataReduction(mock_metadata, mock_parameters)
    assert reduction.data_list is not None
    assert len(reduction.data_list) > 0


def test_data_reduction_1d_detector():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_data_source = MockDataSource(detector="1Ddata", region=(0, 1, 0, 1))
    mock_parameters = MockCorrectionParameters(data_source=mock_data_source)
    reduction = DataReduction(mock_metadata, mock_parameters)
    assert reduction.data_list is not None
    assert len(reduction.data_list) == 1


def test_data_reduction_multiple_polarisations():
    mock_metadata = MockMetadata(polarisation=["up", "down"])
    mock_parameters = MockCorrectionParameters()
    reduction = DataReduction(mock_metadata, mock_parameters)
    assert len(reduction.data_list) == 2


def test_data_reduction_footprint_correction():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_reduction = MockReduction(foot_print_correction=True)
    mock_metadata.sample = MockSample(length=2.0, thickness=1.0, height=1.0)
    mock_parameters = MockCorrectionParameters(reduction=mock_reduction)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_absorption_correction_const():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_reduction = MockReduction(absorption_correction=True, mu_type=AdsorptionTypeCorrection.constValue, mu_value=0)
    mock_metadata.sample = MockSample(length=2.0, thickness=1.0, height=1.0)
    mock_parameters = MockCorrectionParameters(reduction=mock_reduction)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_absorption_correction_typical():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_mu_enum = Mock()
    mock_mu_enum.value = 0.1
    mock_reduction = MockReduction(absorption_correction=True, mu_type=AdsorptionTypeCorrection.typical, mu_enum=mock_mu_enum)
    mock_metadata.sample = MockSample(length=2.0, thickness=1.0, height=1.0)
    mock_parameters = MockCorrectionParameters(reduction=mock_reduction)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_absorption_correction_other():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_reduction = MockReduction(absorption_correction=True, mu_type="somethingElse")
    mock_metadata.sample = MockSample(length=2.0, thickness=1.0, height=1.0)
    mock_parameters = MockCorrectionParameters(reduction=mock_reduction)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_polarisation_correction_not_implemented():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_reduction = MockReduction(polarisation_correction=True)
    mock_parameters = MockCorrectionParameters(reduction=mock_reduction)
    reduction = DataReduction(mock_metadata, mock_parameters)
    with pytest.raises(NotImplementedError):
        _ = reduction.result


def test_data_reduction_normalisation_monitor():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_normalisation = MockNormalisation(monitor=True)
    mock_parameters = MockCorrectionParameters(normalisation=mock_normalisation)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_normalisation_time():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_normalisation = MockNormalisation(time=True)
    mock_parameters = MockCorrectionParameters(normalisation=mock_normalisation)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_background_correction_const():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_background = MockBackground(use_correction=True, correction_type=BackgroundTypeCorrection.constValue, value=0.5)
    mock_parameters = MockCorrectionParameters(background=mock_background)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_background_correction_psd_region():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_background = MockBackground(use_correction=True, correction_type=BackgroundTypeCorrection.psdRegion, region=(0, 1, 0, 1))
    mock_data_source = MockDataSource(detector="2Ddata", region=(0, 1, 0, 1))
    mock_parameters = MockCorrectionParameters(background=mock_background, data_source=mock_data_source)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_background_correction_psd_region_no_overlap():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_background = MockBackground(use_correction=True, correction_type=BackgroundTypeCorrection.psdRegion, region=(2, 3, 2, 3))
    mock_data_source = MockDataSource(detector="2Ddata", region=(0, 1, 0, 1))
    mock_parameters = MockCorrectionParameters(background=mock_background, data_source=mock_data_source)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_background_correction_extra_file():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_background = MockBackground(use_correction=True, correction_type=BackgroundTypeCorrection.extraFile)
    mock_parameters = MockCorrectionParameters(background=mock_background)
    reduction = DataReduction(mock_metadata, mock_parameters)
    with pytest.raises(NotImplementedError):
        _ = reduction.result


def test_data_reduction_intensity_correction_const():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_normalisation = MockNormalisation(intensity_norm=True, intensity_norm_type=IntensityTypeCorrection.constValue, intensity_value=2.0)
    mock_parameters = MockCorrectionParameters(normalisation=mock_normalisation)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None
    assert result[0].result.R is not None


def test_data_reduction_intensity_correction_max():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_normalisation = MockNormalisation(intensity_norm=True, intensity_norm_type=IntensityTypeCorrection.maxValue)
    mock_parameters = MockCorrectionParameters(normalisation=mock_normalisation)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_intensity_correction_max_global():
    mock_metadata = MockMetadata(polarisation=["up", "down"])
    mock_normalisation = MockNormalisation(intensity_norm=True, intensity_norm_type=IntensityTypeCorrection.maxValueGlobal)
    mock_parameters = MockCorrectionParameters(normalisation=mock_normalisation)
    reduction = DataReduction(mock_metadata, mock_parameters)
    result = reduction.result
    assert result is not None


def test_data_reduction_intensity_correction_psd_region():
    mock_metadata = MockMetadata(polarisation=["up"])
    mock_normalisation = MockNormalisation(intensity_norm=True, intensity_norm_type=IntensityTypeCorrection.psdRegion)
    mock_parameters = MockCorrectionParameters(normalisation=mock_normalisation)
    reduction = DataReduction(mock_metadata, mock_parameters)
    with pytest.raises(NotImplementedError):
        _ = reduction.result


def test_create_orso():
    mock_metadata = MockMetadata(file_path="/path/to/test_file.nxs", polarisation=["up"])
    mock_parameters = MockCorrectionParameters()
    reduction = DataReduction(mock_metadata, mock_parameters)
    with patch('converter.reduction.OrsoData') as mock_orso:
        mock_orso_instance = MagicMock()
        mock_orso.return_value = mock_orso_instance
        reduction.create_orso()
        mock_orso.assert_called_once()


def test_create_orso_with_path():
    mock_metadata = MockMetadata(file_path="/path/to/test_file.nxs", polarisation=["up"])
    mock_parameters = MockCorrectionParameters()
    reduction = DataReduction(mock_metadata, mock_parameters)
    with patch('converter.reduction.OrsoData') as mock_orso:
        mock_orso_instance = MagicMock()
        mock_orso.return_value = mock_orso_instance
        reduction.create_orso(path="/output/path")
        mock_orso.assert_called_once()


def test_create_orso_folder_input_file():
    mock_metadata = MockMetadata(file_path="/path/to/test_file.nxs", polarisation=["up"])
    mock_parameters = MockCorrectionParameters()
    reduction = DataReduction(mock_metadata, mock_parameters)
    with patch('converter.reduction.OrsoData') as mock_orso:
        mock_orso_instance = MagicMock()
        mock_orso.return_value = mock_orso_instance
        reduction.create_orso(filename="custom_name", folder_input_file=True)
        mock_orso.assert_called_once()
