import re
import ast
import numpy as np
import pandas as pd

from typing import Iterable
from datetime import datetime
from collections import defaultdict
import nexusformat.nexus.tree as nx
from nexusformat.nexus import nxload

from .datatypes import PolarizationEnum, PersonData, ExperimentData, SampleData, MeasurementData, SlitData, \
    InstrumentSettingsData, PolarisationEfficiencyData
from .metadata import Metadata
from .utils import polarisation_filter, get_polarisation, get_sample_from_str
from .config import POLARISATION_DEVICES, INCIDENT_ANGLE_AXIS, SLIT_DEVICES, MONITOR_DETECTOR_NAME, \
    TIME_DETECTOR_NAME


class NexusFile(Metadata):
    """
    Reader of nexus data

    Attrs:
        file_path:
            The local path to the file on the local filesystem.
    """

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.nxfile = nxload(file_path)

    @property
    def src_path(self) -> str:
        return self.nxfile.file_name

    @property
    def instrument_name(self):
        """
        Returns the NXinstrument instanced stored in this NexusFile.

        Raises:
            ValueError if more than one NXinstrument is found.
        """
        instrument, = self.entry.NXinstrument
        return instrument

    @property
    def instrument(self) -> nx.NXobject:
        """
                Returns this nexusfile's instrument.

                Raises:
                    ValueError if more than one instrument is found.
                """
        instrument, = self.entry.NXinstrument
        return instrument

    @property
    def nxdata(self) -> nx.NXdata:
        """
                Returns this nexusfile's data.

                Raises:
                    ValueError if more than one instrument is found.
                """
        data, = self.entry.NXdata
        return data

    @property
    def entry(self) -> nx.NXentry:
        """
        Returns this nexusfile's entry.

        Raises:
            ValueError if more than one entry is found.
        """
        entry, = self.nxfile.NXentry
        return entry

    @property
    def detectors_list(self) -> list[str]:
        """
        Returns the detector list for data calculation.
        """
        return self.nxdata.signal.split(',')

    @property
    def dev_list(self) -> list[str]:
        """
        Returns the list of scan devices for data calculation.
        """
        return self.nxdata.axes.split(',')

    @property
    def monitor(self) -> np.array:
        """
            Returns the name of monitor devices for data calculation.
        """
        return self.entry.NXmonitor[0].monitor.nxdata

    @property
    def time(self) -> np.array:
        """
            Returns the name of times devices for data calculation.
        """
        return self.entry.NXmonitor[0].time.nxdata

    @property
    def polarisation(self) -> list[PolarizationEnum]:
        """
        Returns the list of scanning device for data calculation.
        """
        return get_polarisation(self.dev_list)

    @property
    def flippers_data(self) -> np.array:
        """
        Returns the data of spin flippers.
        """
        res = [self.nxdata.get(dev).astype('str') for dev in POLARISATION_DEVICES if dev in self.dev_list]
        if res:
            return np.column_stack(res)
        return np.array([])

    def get_dataset(self, detector_name: str, polarisation: PolarizationEnum) -> np.array:
        """
        Returns the list of scanning device for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.nxdata.get(detector_name).nxdata, polarisation)

    def get_dataset_monitor(self, polarisation: PolarizationEnum) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.entry.NXmonitor[0].monitor.nxdata, polarisation)

    def get_dataset_time(self, polarisation: PolarizationEnum) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.entry.NXmonitor[0].time.nxdata, polarisation)

    @property
    def owner(self) -> PersonData:
        """
            Returns the owner of file.
        """
        def filter_user(role: str, users_list: Iterable) -> list:
            return list(filter(lambda item: item.role == role, users_list))
        users = self.entry.NXuser
        user = filter_user('principal_investigator', users)
        user = user[0] if user else filter_user('local_contact', users)[0]
        return PersonData(name=user.get('name'), contact=user.get('email'))

    @property
    def experiment(self) -> ExperimentData:
        """
            Returns the experiment for orso file.
        """
        return ExperimentData(title=self.entry.get('title')[0],
                          instrument=self.instrument_name,
                          start_date=datetime.strptime(str(self.entry.get('start_time')[0]),
                                                       "%Y-%m-%d %H:%M:%S.%f"),
                          proposalID=str(self.entry.get('proposal_id')[0])
                          )

    @property
    def sample(self) -> SampleData:
        """
        Returns the experiment for orso file.
        """
        sample, = self.entry.NXsample
        sample2 = get_sample_from_str(self.instrument.all_devices.system.Sample.samples,
                            sample.samplename)
        return sample2

        #return SampleData(name=sample.samplename,
        #                  category=sample.category,
        #                  composition=sample.composition,
        #                  description=sample.description,
        #                  length=sample.length,
        #                  height=sample.height,
        #                  thickness=sample.thickness
        #                  ) it will work after Nicos modernisation

    def measurement(self, polarisation: PolarizationEnum) -> MeasurementData:
        """
            Returns the Measurment data
        """
        return MeasurementData(instrument_settings=self.instrument_settings(polarisation),
                           data_files=self.src_path)

    @property
    def slit_configuration(self) -> SlitData:
        """
            Returns the Slits positions
        """
        slit1_name, slit2_name = SLIT_DEVICES
        return SlitData( slit1_width = self.instrument.get(slit1_name).x_gap[0].nxdata,
                         slit1_position = self.instrument.get(slit1_name).z[0].nxdata,
                         slit2_width = self.instrument.get(slit2_name).x_gap[0].nxdata,
                         slit2_position = self.instrument.get(slit2_name).z[0].nxdata)

    def instrument_settings(self, polarisation: PolarizationEnum) -> InstrumentSettingsData:
        """
        Returns the instrument setting data.
        """
        theta_angles = self.nxdata.get(INCIDENT_ANGLE_AXIS)
        #efficiency = self.instrument.polarizer.get('efficiency')
        #instrument_settings.incident_polarization = POLARISATION if efficiency is None \
        #    else efficiency[0].nxdata
        polarization_efficiency = PolarisationEfficiencyData()
        return InstrumentSettingsData(incident_angle=(theta_angles.min(), theta_angles.max()),
                                      angle_unit=theta_angles.units,
                                      wavelength=self.instrument.monochromator.wavelength[0].nxdata,
                                      wavelength_unit='A',
                                      polarization=polarisation,
                                      slit_configuration=self.slit_configuration,
                                      polarization_efficiency=polarization_efficiency
                                    )


class ScanDataReader:
    """
        Class for parsing of Nicos scan file
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata = defaultdict(dict)
        self.header = []
        self.header_units = []
        self.df = pd.DataFrame()
        self._parse_file()

    def _parse_file(self):
        header = []
        header_units = []
        data_lines = []
        current_section = None
        table_started = False
        with open(self.file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Section headers
                if line.startswith('###'):
                    current_section = line.strip('# ').strip()
                    if current_section.startswith('NICOS data file'):
                        self.metadata['General']['Date'] = current_section.split('at ')[1]
                        current_section = 'General'
                    continue

                # Metadata line
                if line.startswith('#') and current_section != 'Scan data':
                    if ':' in line:
                        keyval = line.lstrip('#').strip()
                        key, value = map(str.strip, keyval.split(':', 1))
                        if current_section:
                            self.metadata[current_section][key] = value
                        else:
                            self.metadata['General'][key] = value
                    continue

                # Start of data table
                if line.startswith('#') and not table_started:
                    header = re.split(r'\t', line.strip('# '))
                    table_started = True
                    continue

                if line.startswith('#') and table_started:
                    header_units = re.split(r'\t', line.strip('# '))
                    table_started = True
                    continue

                # Data rows
                if table_started:
                    # split both tabs and semicolons
                    parts = re.split(r'\t', line.strip('# '))
                    data_lines.append(parts)
        self.header = header
        self.header_units = header_units
        self.df = pd.DataFrame(data_lines, columns=header)

    def get_devices(self) -> list[str]:
        index = self.header.index(';')
        return self.header[:index]

    def get_detectors(self) -> list[str]:
        index_end = next((i for i, item in enumerate(self.header) if item.startswith('file')), -1)
        index_start = self.header.index(';') + 1

        return self.header[index_start:index_end] if (';' not in
                                                      self.header[index_start:index_end]) \
            else self.header[index_start:index_end - 1]


class ScanDataFile(Metadata):
    """
        Reader of Nicos scan file data

        Attrs:
            file_path:
                The local path to the file on the local filesystem.
    """

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.scan_file = ScanDataReader(file_path)

    @property
    def metadata(self) -> dict:
        """
            Returns this scanfile's metadata.
        """
        return self.scan_file.metadata

    @property
    def dataset(self) -> pd.DataFrame:
        """
            Returns this scanfile's pandas data frame.
        """
        return self.scan_file.df

    @property
    def detectors_list(self) -> list[str]:
        """
        Returns the detector list for data calculation.
        """
        return self.scan_file.get_detectors()

    @property
    def dev_list(self) -> list[str]:
        """
        Returns the list of scan devices for data calculation.
        """
        return self.scan_file.get_devices()

    @property
    def monitor(self) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return self.dataset[MONITOR_DETECTOR_NAME].to_numpy().astype('float')

    @property
    def time(self) -> np.array:
        """
        Returns the data of times devices for data calculation.
        """
        return self.dataset[TIME_DETECTOR_NAME].to_numpy().astype('float')

    @property
    def polarisation(self) -> list[PolarizationEnum]:
        """
        Returns the list of scanning device for data calculation.
        """
        return get_polarisation(self.dev_list)

    @property
    def flippers_data(self) -> np.array:
        """
            Returns the data of spin flippers.
        """
        res = [self.dataset[dev].to_numpy() for dev in POLARISATION_DEVICES if dev in self.dev_list]
        if res:
            return np.column_stack(res)
        return np.array([])

    def get_dataset(self, detector_name: str, polarisation: PolarizationEnum) -> np.array:
        """
        Returns the list of scanning device for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.dataset[detector_name].to_numpy().astype('float'),
                                   polarisation)

    def get_dataset_monitor(self, polarisation: PolarizationEnum) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.monitor, polarisation)

    def get_dataset_time(self, polarisation: PolarizationEnum) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.time, polarisation)

    @property
    def owner(self) -> PersonData:
        """
        Returns the owner of file for orso file.
        """
        user = {}
        users_str = self.metadata['Experiment information']['Exp_users']
        if '{' in users_str and '}' in users_str:
            users_str = ast.literal_eval(users_str)
            if users_str is isinstance(users_str, Iterable):
                user = ast.literal_eval(users_str)[0]
            else:
                user = users_str
        else:
            user['name'] = users_str.split(',')[0]
        return PersonData(name=user.get('name'), contact=user.get('email'))

    @property
    def experiment(self) -> ExperimentData:
        """
        Returns the experiment for orso file.
        """
        instrument_setup = {key.split('_')[1]: value for key, value in self.metadata['Instrument setup'].items()}
        return ExperimentData(title=self.metadata['Experiment information']['Exp_title'],
                              instrument=instrument_setup['instrument'],
                              start_date=datetime.strptime(self.metadata['General']['Date'],
                                                           "%Y-%m-%d %H:%M:%S"),
                              proposalID=str(self.metadata['Experiment information']['Exp_proposal']),
                              doi=instrument_setup['doi'],
                              probe='neutron'
                              )

    @property
    def sample(self) -> SampleData:
        """
        Returns the experiment for orso file.
        """
        sample = {key.split('_')[1]: value
                  for key, value in self.metadata['Sample and alignment'].items()}

        sample2 = get_sample_from_str(sample['samples'],
                                      sample['samplename'])
        return sample2

        #return SampleData(name=sample['samplename'],
        #                  category=sample['category'],
        #                  composition=sample['composition'],
        #                  description=sample['description'],
        #                  length=float(sample['length']),
        #                  height=float(sample['height']),
        #                  thickness=float(sample['thickness'])
        #                  )

    @property
    def slit_configuration(self) -> SlitData:
        """
            Returns the Slits positions
        """
        slit1_name, slit2_name = SLIT_DEVICES
        values = self.metadata['Device positions and sample environment state']
        return SlitData(slit1_width=float(values.get(f'{slit2_name}_value').split()[2]),
                        slit1_position=float(values.get(f'd_{slit1_name}_value').split()[0]),
                        slit2_width=float(values.get(f'{slit2_name}_value').split()[2]),
                        slit2_position=float(values.get(f'd_{slit2_name}_value').split()[0]),
                        units=values.get(f'd_{slit1_name}_value').split()[1]
                        )

    def instrument_settings(self, polarisation: PolarizationEnum) -> InstrumentSettingsData:
        """
        Returns the instrument setting data.
        """
        theta_angles = self.dataset[INCIDENT_ANGLE_AXIS].to_numpy()
        units = self.scan_file.header_units[self.scan_file.header.index(INCIDENT_ANGLE_AXIS)]
        wavelength = self.metadata['Device positions and sample environment state']['wavelength_value']
        wavelength, wavelength_unit = float(wavelength.split()[0]), wavelength.split()[1]
        #efficiency = self.instrument.polarizer.get('efficiency')
        #instrument_settings.incident_polarization = POLARISATION if efficiency is None \
        #    else efficiency[0].nxdata
        polarization_efficiency = PolarisationEfficiencyData()
        return InstrumentSettingsData(incident_angle=(theta_angles.min(), theta_angles.max()),
                                      angle_unit=units,
                                      wavelength=wavelength,
                                      wavelength_unit=wavelength_unit,
                                      polarization=polarisation,
                                      incident_intensity=None,
                                      slit_configuration=self.slit_configuration,
                                      polarization_efficiency=polarization_efficiency
                                    )

    def measurement(self, polarisation: PolarizationEnum) -> MeasurementData:
        """
        Returns the experiment for orso file.
        """
        return MeasurementData(instrument_settings=self.instrument_settings(polarisation),
                           data_files=self.metadata['General']['filepath'])


def get_data(file_path: str) -> Metadata:
    if file_path.endswith('.nxs'):
        return NexusFile(file_path)
    elif file_path.endswith('.dat'):
        return ScanDataFile(file_path)
    else:
        raise ValueError("Unknown file type")
