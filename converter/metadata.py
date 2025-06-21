import numpy as np
from abc import abstractmethod, ABC
from .datatypes import (SampleData, ExperimentData, MeasurementData,
                                 InstrumentSettingsData, PolarizationEnum, PersonData, SlitData)


class Metadata(ABC):
    """
        An ABC for classes that store metadata parsed from data files. This defines
        the properties that must be implemented by parsing classes.
    """

    def __init__(self, file_path):
        self.file_path = file_path

    @property
    @abstractmethod
    def detectors_list(self) -> list[str]:
        """
            Returns the detector list for data calculation.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def dev_list(self) -> list[str]:
        """
            Returns the list of scan devices for data calculation.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def monitor(self) -> np.array:
        """
            Returns the data of monitor devices for data calculation.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def time(self) -> np.array:
        """
            Returns the data of times devices for data calculation.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def polarisation(self) -> list[PolarizationEnum]:
        """
            Returns the list of scanning device for data calculation.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def flippers_data(self) -> np.array:
        """
            Returns the data of spin flippers.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_dataset_monitor(self, polarisation: PolarizationEnum) -> np.array:
        """
            Returns the data of monitor devices for data calculation.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_dataset_time(self, polarisation: PolarizationEnum) -> np.array:
        """
        Returns the data of time devices for data calculation.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_dataset(self, detector_name: str, polarisation: PolarizationEnum) -> np.array:
        """
        Returns the array with detectors counts for polarisation value.
        """

        raise NotImplementedError()

    #orso data
    @property
    @abstractmethod
    def owner(self) -> PersonData:
        """
        Returns the owner of file data.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def experiment(self) -> ExperimentData:
        """
        Returns the experiment data.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def sample(self) -> SampleData:
        """
        Returns the Sample data.
        """
        raise NotImplementedError()

    @abstractmethod
    def measurement(self, polarisation: PolarizationEnum) -> MeasurementData:
        """
        Returns the Measurement data.
        """
        raise NotImplementedError()

    @abstractmethod
    def instrument_settings(self, polarisation: PolarizationEnum) -> InstrumentSettingsData:
        """
        Returns the instrument setting data.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def slit_configuration(self) -> SlitData:
        """
            Returns the slits data.
        """
        raise NotImplementedError()
