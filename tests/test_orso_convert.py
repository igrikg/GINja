import numpy as np
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from converter.orso_convert import OrsoData, get_header_orso, get_measurement_orso
from converter.datatypes import (
    DataSet, DataSetMetadata, DataSetOutput, MeasurementData,
    CorrectionParameters, DataSourceConfig, NormalisationConfig, ReductionConfig, BackgroundConfig,
    PersonData, SampleData, ExperimentData, InstrumentSettingsData,
    PolarizationEnum, SlitData, AdsorptionTypeCorrection, IntensityTypeCorrection, BackgroundTypeCorrection,
    MuDataEnum
)


def create_mock_data_set(polarization=PolarizationEnum.unpolarized):
    owner = PersonData(name="Test User", affiliation="Test Institute")
    experiment = ExperimentData(
        title="Test Experiment",
        instrument="Test Instrument",
        start_date=datetime(2024, 1, 1)
    )
    sample = SampleData(
        name="Test Sample",
        length=10.0,
        height=5.0,
        thickness=2.0,
        units="mm"
    )
    header = DataSetMetadata(owner=owner, experiment=experiment, sample=sample)
    
    instrument_settings = InstrumentSettingsData(
        incident_angle=(0.0, 90.0),
        angle_unit="degree",
        wavelength=5.0,
        wavelength_unit="A",
        slit_configuration=SlitData(
            slit1_width=0.1,
            slit2_width=0.1,
            slit1_position=0,
            slit2_position=100,
            units="mm"
        ),
        polarization=polarization
    )
    
    measurement = MeasurementData(
        instrument_settings=instrument_settings,
        data_files=["file1.dat", "file2.dat"]
    )
    
    theta = np.array([0.1, 0.2, 0.3])
    time = np.array([1.0, 2.0, 3.0])
    monitor = np.array([100, 200, 300])
    counts = np.array([10, 20, 30])
    e_counts = np.sqrt(counts)
    background = np.array([1, 1, 1])
    e_background = np.array([1, 1, 1])
    result = DataSetOutput(
        Q=np.array([0.1, 0.2, 0.3]),
        dQ=np.array([0.01, 0.02, 0.03]),
        R=np.array([1.0, 2.0, 3.0]),
        dR=np.array([0.1, 0.2, 0.3])
    )
    
    return DataSet(
        header=header,
        measurement=measurement,
        theta=theta,
        time=time,
        monitor=monitor,
        counts=counts,
        e_counts=e_counts,
        background=background,
        e_background=e_background,
        result=result
    )


def create_mock_parameters(
    detector="detector1",
    region=None,
    foot_print_correction=False,
    absorption_correction=False,
    polarisation_correction=False,
    time=True,
    monitor=True,
    intensity_norm=False,
    intensity_norm_type=IntensityTypeCorrection.constValue,
    intensity_value=1.0,
    background_use_correction=False,
    background_correction_type=BackgroundTypeCorrection.constValue,
    background_value=0.0,
    mu_type=AdsorptionTypeCorrection.constValue,
    mu_value=0,
    mu_enum=MuDataEnum.glass
):
    data_source = DataSourceConfig(detector=detector, region=region)
    normalisation = NormalisationConfig(
        time=time,
        monitor=monitor,
        intensity_norm=intensity_norm,
        intensity_norm_type=intensity_norm_type,
        intensity_value=intensity_value
    )
    reduction = ReductionConfig(
        foot_print_correction=foot_print_correction,
        absorption_correction=absorption_correction,
        polarisation_correction=polarisation_correction,
        mu_type=mu_type,
        mu_value=mu_value,
        mu_enum=mu_enum
    )
    background = BackgroundConfig(
        use_correction=background_use_correction,
        correction_type=background_correction_type,
        value=background_value
    )
    return CorrectionParameters(
        data_source=data_source,
        normalisation=normalisation,
        reduction=reduction,
        background=background,
        program_call="test_program"
    )


def test_get_header_orso():
    owner = PersonData(name="Test User", affiliation="Test Institute")
    experiment = ExperimentData(
        title="Test Experiment",
        instrument="Test Instrument",
        start_date=datetime(2024, 1, 1)
    )
    sample = SampleData(
        name="Test Sample",
        length=10.0,
        height=5.0,
        thickness=2.0,
        units="mm"
    )
    header = DataSetMetadata(owner=owner, experiment=experiment, sample=sample)
    
    orso_owner, orso_exp, orso_sample = get_header_orso(header)
    
    assert orso_owner.name == "Test User"
    assert orso_owner.affiliation == "Test Institute"
    assert orso_exp.title == "Test Experiment"
    assert orso_exp.instrument == "Test Instrument"
    assert orso_sample.name == "Test Sample"
    assert orso_sample.size.x == 10.0
    assert orso_sample.size.y == 5.0
    assert orso_sample.size.z == 2.0
    assert orso_sample.size.unit == "mm"


def test_get_measurement_orso():
    instrument_settings = InstrumentSettingsData(
        incident_angle=(0.0, 90.0),
        angle_unit="degree",
        wavelength=5.0,
        wavelength_unit="A",
        slit_configuration=SlitData(
            slit1_width=0.1,
            slit2_width=0.1,
            slit1_position=0,
            slit2_position=100,
            units="mm"
        ),
        polarization=PolarizationEnum.unpolarized
    )
    
    measurement = MeasurementData(
        instrument_settings=instrument_settings,
        data_files=["file1.dat"]
    )
    
    orso_meas = get_measurement_orso(measurement)
    
    assert orso_meas is not None
    assert orso_meas.data_files == ["file1.dat"]


def test_orso_data_init():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters()
    orso_data = OrsoData([dataset], parameters)
    assert orso_data is not None


def test_orso_data_columns():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters()
    orso_data = OrsoData([dataset], parameters)
    columns = orso_data.columns
    
    assert len(columns) == 4
    assert columns[0].name == "Q"
    assert columns[1].error_of == "Q"
    assert columns[2].name == "R"
    assert columns[3].error_of == "R"


def test_orso_data_reduction_no_corrections():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        foot_print_correction=False,
        absorption_correction=False,
        polarisation_correction=False,
        time=False,
        monitor=False,
        intensity_norm=False,
        background_use_correction=False
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    assert reduction is not None
    combined = " ".join(reduction.corrections)
    assert "Calculate Q from Angle" in combined
    assert "Calculate dQ from Slit parameters" in combined
    assert "Calculate dR like Poisson distribution" in combined


def test_orso_data_reduction_foot_print():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(foot_print_correction=True)
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    assert "Made foot print correction with trapezoid beam" in reduction.corrections


def test_orso_data_reduction_polarisation():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(polarisation_correction=True)
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    assert "Made polarisation correction" in reduction.corrections


def test_orso_data_reduction_absorption_const():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        absorption_correction=True,
        mu_type=AdsorptionTypeCorrection.constValue,
        mu_value=0
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made absorption correction" in combined
    assert "mu = 0" in combined


def test_orso_data_reduction_absorption_typical():
    dataset = create_mock_data_set()
    mock_mu_enum = MagicMock()
    mock_mu_enum.name = "glass"
    mock_mu_enum.value = 0.1
    parameters = create_mock_parameters(
        absorption_correction=True,
        mu_type=AdsorptionTypeCorrection.typical,
        mu_enum=mock_mu_enum
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made absorption correction" in combined
    assert "mu(glass)" in combined


def test_orso_data_reduction_absorption_other():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        absorption_correction=True,
        mu_type="other"
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made absorption correction" in combined


def test_orso_data_reduction_time():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(time=True)
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    assert "Made time normalisation" in reduction.corrections


def test_orso_data_reduction_monitor():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(monitor=True)
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    assert "Made monitor counts normalisation" in reduction.corrections


def test_orso_data_reduction_intensity_const():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        intensity_norm=True,
        intensity_norm_type=IntensityTypeCorrection.constValue,
        intensity_value=2.0
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made intensity normalisation" in combined
    assert "constant value 2.0" in combined


def test_orso_data_reduction_intensity_max():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        intensity_norm=True,
        intensity_norm_type=IntensityTypeCorrection.maxValue
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made intensity normalisation" in combined
    assert "maximum intensity point in current dataset" in combined


def test_orso_data_reduction_intensity_max_global():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        intensity_norm=True,
        intensity_norm_type=IntensityTypeCorrection.maxValueGlobal
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made intensity normalisation" in combined
    assert "maximum intensity point of all datasets" in combined


def test_orso_data_reduction_intensity_psd():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        intensity_norm=True,
        intensity_norm_type=IntensityTypeCorrection.psdRegion,
        intensity_value=1.0
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made intensity normalisation" in combined


def test_orso_data_reduction_background_const():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        background_use_correction=True,
        background_correction_type=BackgroundTypeCorrection.constValue,
        background_value=0.5
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made background correction" in combined
    assert "with constant value 0.5" in combined


def test_orso_data_reduction_background_extra_file():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        background_use_correction=True,
        background_correction_type=BackgroundTypeCorrection.extraFile,
        background_value=0.0
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made background correction" in combined
    assert "from file" in combined


def test_orso_data_reduction_background_psd_region():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        background_use_correction=True,
        background_correction_type=BackgroundTypeCorrection.psdRegion
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    combined = " ".join(reduction.corrections)
    assert "Made background correction" in combined
    assert "from PSD" in combined


def test_orso_data_orso_dataset():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters()
    orso_data = OrsoData([dataset], parameters)
    orso_dataset = orso_data.orso_dataset
    
    assert len(orso_dataset) == 1


def test_orso_data_orso_dataset_multiple():
    dataset1 = create_mock_data_set()
    dataset2 = create_mock_data_set()
    parameters = create_mock_parameters()
    orso_data = OrsoData([dataset1, dataset2], parameters)
    orso_dataset = orso_data.orso_dataset
    
    assert len(orso_dataset) == 2


def test_orso_data_save():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters()
    orso_data = OrsoData([dataset], parameters)
    
    with patch('converter.orso_convert.save_orso') as mock_save:
        orso_data.save("/tmp/test_output")
        mock_save.assert_called_once()


def test_orso_data_reduction_detector_with_region():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        detector="detector1",
        region=(0, 10, 0, 10)
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    assert "Collect intensity from detector1" in reduction.corrections[0]
    assert "from region" in reduction.corrections[0]


def test_orso_data_reduction_detector_no_region():
    dataset = create_mock_data_set()
    parameters = create_mock_parameters(
        detector="detector1",
        region=None
    )
    orso_data = OrsoData([dataset], parameters)
    reduction = orso_data.reduction
    
    assert "Collect intensity from detector1" in reduction.corrections[0]
