import numpy as np
import pytest
from datetime import datetime
from unittest.mock import patch
from converter.metadata import Metadata
from converter.datatypes import (
    SampleData, ExperimentData, MeasurementData,
    InstrumentSettingsData, PolarizationEnum, PersonData, SlitData
)


class ConcreteMetadata(Metadata):
    def __init__(self, file_path="test.nxs", fix_polarisation=False):
        super().__init__(file_path, fix_polarisation)

    @property
    def detectors_list(self):
        return ["detector1", "detector2"]

    @property
    def dev_list(self):
        return ["device1", "device2"]

    @property
    def monitor(self):
        return np.array([1, 2, 3])

    @property
    def time(self):
        return np.array([1.0, 2.0, 3.0])

    @property
    def polarisation(self):
        return [PolarizationEnum.unpolarized]

    @property
    def flippers_data(self):
        return np.array([[0, 1], [1, 0]])

    def get_dataset_monitor(self, polarisation):
        return np.array([10, 20, 30])

    def get_dataset_time(self, polarisation):
        return np.array([1.0, 2.0, 3.0])

    def get_dataset(self, detector_name, polarisation):
        return np.array([[1, 2], [3, 4], [5, 6]])

    @property
    def owner(self):
        return PersonData(name="Test User", affiliation="Test Institute")

    @property
    def experiment(self):
        return ExperimentData(
            title="Test Experiment",
            instrument="Test Instrument",
            start_date=datetime(2024, 1, 1)
        )

    @property
    def sample(self):
        return SampleData(name="Test Sample")

    def measurement(self, polarisation):
        return MeasurementData(
            instrument_settings=InstrumentSettingsData(
                incident_angle=(0.0, 90.0),
                angle_unit="degree",
                wavelength=5.0,
                slit_configuration=SlitData(
                    slit1_width=0.1,
                    slit2_width=0.1,
                    slit1_position=0,
                    slit2_position=100
                )
            ),
            data_files=["file1.dat"]
        )

    def instrument_settings(self, polarisation):
        return InstrumentSettingsData(
            incident_angle=(0.0, 90.0),
            angle_unit="degree",
            wavelength=5.0,
            slit_configuration=SlitData(
                slit1_width=0.1,
                slit2_width=0.1,
                slit1_position=0,
                slit2_position=100
            )
        )

    @property
    def slit_configuration(self):
        return SlitData(
            slit1_width=0.1,
            slit2_width=0.1,
            slit1_position=0,
            slit2_position=100
        )


def test_metadata_init():
    metadata = ConcreteMetadata()
    assert metadata.file_path == "test.nxs"
    assert metadata._fix_polarisation is False


def test_metadata_init_with_fix_polarisation():
    metadata = ConcreteMetadata(fix_polarisation=True)
    assert metadata._fix_polarisation is True


def test_metadata_detectors_list():
    metadata = ConcreteMetadata()
    assert metadata.detectors_list == ["detector1", "detector2"]


def test_metadata_dev_list():
    metadata = ConcreteMetadata()
    assert metadata.dev_list == ["device1", "device2"]


def test_metadata_monitor():
    metadata = ConcreteMetadata()
    np.testing.assert_array_equal(metadata.monitor, np.array([1, 2, 3]))


def test_metadata_time():
    metadata = ConcreteMetadata()
    np.testing.assert_array_equal(metadata.time, np.array([1.0, 2.0, 3.0]))


def test_metadata_polarisation():
    metadata = ConcreteMetadata()
    assert metadata.polarisation == [PolarizationEnum.unpolarized]


def test_metadata_flippers_data():
    metadata = ConcreteMetadata()
    np.testing.assert_array_equal(metadata.flippers_data, np.array([[0, 1], [1, 0]]))


def test_metadata_get_dataset_monitor():
    metadata = ConcreteMetadata()
    result = metadata.get_dataset_monitor(PolarizationEnum.unpolarized)
    np.testing.assert_array_equal(result, np.array([10, 20, 30]))


def test_metadata_get_dataset_time():
    metadata = ConcreteMetadata()
    result = metadata.get_dataset_time(PolarizationEnum.unpolarized)
    np.testing.assert_array_equal(result, np.array([1.0, 2.0, 3.0]))


def test_metadata_get_dataset():
    metadata = ConcreteMetadata()
    result = metadata.get_dataset("detector1", PolarizationEnum.unpolarized)
    np.testing.assert_array_equal(result, np.array([[1, 2], [3, 4], [5, 6]]))


def test_metadata_owner():
    metadata = ConcreteMetadata()
    owner = metadata.owner
    assert owner.name == "Test User"
    assert owner.affiliation == "Test Institute"


def test_metadata_experiment():
    metadata = ConcreteMetadata()
    exp = metadata.experiment
    assert exp.title == "Test Experiment"
    assert exp.instrument == "Test Instrument"


def test_metadata_sample():
    metadata = ConcreteMetadata()
    sample = metadata.sample
    assert sample.name == "Test Sample"


def test_metadata_measurement():
    metadata = ConcreteMetadata()
    measurement = metadata.measurement(PolarizationEnum.unpolarized)
    assert measurement.instrument_settings.wavelength == 5.0


def test_metadata_instrument_settings():
    metadata = ConcreteMetadata()
    settings = metadata.instrument_settings(PolarizationEnum.unpolarized)
    assert settings.wavelength == 5.0


def test_metadata_slit_configuration():
    metadata = ConcreteMetadata()
    slit = metadata.slit_configuration
    assert slit.slit1_width == 0.1
    assert slit.slit2_width == 0.1


def test_metadata_file_path():
    metadata = ConcreteMetadata(file_path="/path/to/file.nxs")
    assert metadata.file_path == "/path/to/file.nxs"


def test_metadata_abstract_not_implemented():
    from converter.metadata import Metadata
    
    class PartialMetadata(Metadata):
        pass
    
    with pytest.raises(TypeError):
        PartialMetadata()


def test_metadata_abstract_methods_raise_not_implemented():
    from converter.metadata import Metadata
    
    class TestMetadata(Metadata):
        def __init__(self):
            self.file_path = "test.nxs"
            self._fix_polarisation = False
        
        @property
        def detectors_list(self):
            return Metadata.detectors_list.fget(self)
        
        @property
        def dev_list(self):
            return Metadata.dev_list.fget(self)
        
        @property
        def monitor(self):
            return Metadata.monitor.fget(self)
        
        @property
        def time(self):
            return Metadata.time.fget(self)
        
        @property
        def polarisation(self):
            return Metadata.polarisation.fget(self)
        
        @property
        def flippers_data(self):
            return Metadata.flippers_data.fget(self)
        
        @property
        def owner(self):
            return Metadata.owner.fget(self)
        
        @property
        def experiment(self):
            return Metadata.experiment.fget(self)
        
        @property
        def sample(self):
            return Metadata.sample.fget(self)
        
        @property
        def slit_configuration(self):
            return Metadata.slit_configuration.fget(self)
        
        def get_dataset_monitor(self, polarisation):
            return Metadata.get_dataset_monitor(self, polarisation)
        
        def get_dataset_time(self, polarisation):
            return Metadata.get_dataset_time(self, polarisation)
        
        def get_dataset(self, detector_name, polarisation):
            return Metadata.get_dataset(self, detector_name, polarisation)
        
        def measurement(self, polarisation):
            return Metadata.measurement(self, polarisation)
        
        def instrument_settings(self, polarisation):
            return Metadata.instrument_settings(self, polarisation)
    
    test_meta = TestMetadata()
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.detectors_list
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.dev_list
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.monitor
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.time
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.polarisation
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.flippers_data
    
    with pytest.raises(NotImplementedError):
        test_meta.get_dataset_monitor(PolarizationEnum.unpolarized)
    
    with pytest.raises(NotImplementedError):
        test_meta.get_dataset_time(PolarizationEnum.unpolarized)
    
    with pytest.raises(NotImplementedError):
        test_meta.get_dataset("det", PolarizationEnum.unpolarized)
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.owner
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.experiment
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.sample
    
    with pytest.raises(NotImplementedError):
        test_meta.measurement(PolarizationEnum.unpolarized)
    
    with pytest.raises(NotImplementedError):
        test_meta.instrument_settings(PolarizationEnum.unpolarized)
    
    with pytest.raises(NotImplementedError):
        _ = test_meta.slit_configuration
