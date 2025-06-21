"""
Program to create  ORSO type for Nano Optics Berlin.
"""
import os
import re
import ast
import itertools
import numpy as np
import argparse
import sys
import pandas as pd
from datetime import datetime
from collections import defaultdict

import nexusformat.nexus.tree as nx
from nexusformat.nexus import nxload
from abc import abstractmethod
from orsopy.fileio import (OrsoDataset, Value, DataSource, Reduction, Software, Column, ErrorColumn, Orso, save_orso,
                           ValueVector, ValueRange,Sample, Polarization)

from .orso import Person, Measurement, InstrumentSettings, Experiment
from converter.config import POLARISATION_DEVICES, INCIDENT_ANGLE_AXIS, SLIT_DEVICES, POLARISATION, MONITOR_DETECTOR_NAME, \
    TIME_DETECTOR_NAME, INTENSITY

from converter.utils import polarisation_filter

__version__ = "0.1.0"


class Metadata:
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
    def polarisation(self) -> list[Polarization]:
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
    def get_dataset_monitor(self, polarisation: Polarization) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_dataset_time(self, polarisation: Polarization) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_dataset(self, detector_name: str, polarisation: Polarization) -> np.array:
        """
        Returns the array with detectors counts for polarisation value.
        """

        raise NotImplementedError()

    #orso data
    @property
    @abstractmethod
    def owner(self) -> Person:
        """
        Returns the owner of file for orso file.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def experiment(self) -> Experiment:
        """
        Returns the experiment for orso file.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def sample(self) -> Sample:
        """
        Returns the experiment for orso file.
        """
        raise NotImplementedError()

    @abstractmethod
    def measurement(self, polarisation: Polarization) -> Measurement:
        """
        Returns the experiment for orso file.
        """
        raise NotImplementedError()

    @abstractmethod
    def instrument_settings(self, polarisation: Polarization) -> InstrumentSettings:
        """
        Returns the experiment for orso file.
        """
        raise NotImplementedError()


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
    def polarisation(self) -> list[Polarization]:
        """
        Returns the list of scanning device for data calculation.
        """
        res = [('m', 'p') if dev in self.dev_list else ('o', 'o')
               for dev in POLARISATION_DEVICES]
        combinations = {Polarization(''.join(combo)) for combo in itertools.product(*res) if ''.join(combo) != 'oo'}
        return list(combinations) if combinations else [Polarization.unpolarized]

    @property
    def flippers_data(self) -> np.array:
        """
        Returns the data of spin flippers.
        """
        res = [self.nxdata.get(dev).astype('str') for dev in POLARISATION_DEVICES if dev in self.dev_list]
        return np.column_stack(res)

    def get_dataset(self, detector_name: str, polarisation: Polarization) -> np.array:
        """
        Returns the list of scanning device for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.nxdata.get(detector_name).nxdata, polarisation)

    def get_dataset_monitor(self, polarisation: Polarization) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.entry.NXmonitor[0].monitor.nxdata, polarisation)

    def get_dataset_time(self, polarisation: Polarization) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.entry.NXmonitor[0].time.nxdata, polarisation)

    @property
    def owner(self) -> Person:
        """
        Returns the owner of file for orso file.
        """
        filter_user = lambda role, users: list(filter(lambda item: item.role == role, users))
        users = self.entry.NXuser
        user = filter_user('principal_investigator', users)
        user = user[0] if user else filter_user('local_contact', users)[0]
        return Person(name=user.get('name'), contact=user.get('email'))

    @property
    def experiment(self) -> Experiment:
        """
        Returns the experiment for orso file.
        """
        return Experiment(title=self.entry.get('title')[0], instrument=self.instrument_name, probe='neutron',
                          start_date=datetime.strptime(str(self.entry.get('start_time')[0]),
                                                       "%Y-%m-%d %H:%M:%S.%f"),
                          proposalID=str(self.entry.get('proposal_id')[0]))

    @property
    def sample(self) -> Sample:
        """
        Returns the experiment for orso file.
        """
        sample, = self.entry.NXsample
        return Sample(name=sample.samplename, category=sample.category,
                      composition=sample.composition, description=sample.description,
                      size=ValueVector(x=sample.length, y=sample.height, z=sample.thickness, unit="mm")
                      )

    def measurement(self, polarisation: Polarization) -> Measurement:
        """
        Returns the experiment for orso file.
        """
        return Measurement(instrument_settings=self.instrument_settings(polarisation),
                           data_files=self.src_path)

    def slit_configuration(self) -> list[tuple[float]]:
        get_data = lambda slitname: (self.instrument.get(slitname).z[0].nxdata,
                                     self.instrument.get(slitname).x_gap[0].nxdata)
        return [get_data(slit) for slit in SLIT_DEVICES]

    def instrument_settings(self, polarisation: Polarization) -> InstrumentSettings:
        """
        Returns the experiment for orso file.
        """
        theta_angles = self.nxdata.get(INCIDENT_ANGLE_AXIS)
        incident_angle = ValueRange(theta_angles.min(), theta_angles.max(), theta_angles.units)

        instrument_settings = InstrumentSettings(incident_angle=incident_angle,
                                                 wavelength=
                                                 self.instrument.monochromator.wavelength[
                                                     0].nxdata,
                                                 polarization=polarisation)
        slitconfig = self.slit_configuration()
        instrument_settings.slit_configuration = {
            "divergence_distance": Value(slitconfig[0][0], "mm"),
            "divergence_opening": Value(slitconfig[0][1], "mm"),
            "size_distance": Value(slitconfig[1][0], "mm"),
            "size_opening": Value(slitconfig[1][1], "mm"),
        }
        instrument_settings.incident_intensity = None
        efficiency = self.instrument.polarizer.get('efficiency')
        instrument_settings.incident_polarization = POLARISATION if efficiency is None \
            else efficiency[0].nxdata
        return instrument_settings


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
        self.scanfile = ScanDataReader(file_path)

    @property
    def metadata(self) -> dict:
        """
            Returns this scanfile's metadata.
        """
        return self.scanfile.metadata

    @property
    def dataset(self) -> pd.DataFrame:
        """
            Returns this scanfile's pandas data frame.
        """
        return self.scanfile.df

    @property
    def detectors_list(self) -> list[str]:
        """
        Returns the detector list for data calculation.
        """
        return self.scanfile.get_detectors()

    @property
    def dev_list(self) -> list[str]:
        """
        Returns the list of scan devices for data calculation.
        """
        return self.scanfile.get_devices()

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
        return self.dataset[TIME_DETECTOR_NAME].astype('float')

    @property
    def polarisation(self) -> list[Polarization]:
        """
        Returns the list of scanning device for data calculation.
        """
        res = [('m', 'p') if dev in self.dev_list else ('o', 'o')
               for dev in POLARISATION_DEVICES]
        combinations = {Polarization(''.join(combo)) for combo in itertools.product(*res) if ''.join(combo) != 'oo'}
        return list(combinations) if combinations else [Polarization.unpolarized]

    @property
    def flippers_data(self) -> np.array:
        """
        Returns the data of spin flippers.
        """
        res = [self.dataset[dev].to_numpy() for dev in POLARISATION_DEVICES if dev in self.dev_list]
        return np.column_stack(res)

    def get_dataset(self, detector_name: str, polarisation: Polarization) -> np.array:
        """
        Returns the list of scanning device for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.dataset[detector_name].to_numpy().astype('float'), polarisation)

    def get_dataset_monitor(self, polarisation: Polarization) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.monitor, polarisation)

    def get_dataset_time(self, polarisation: Polarization) -> np.array:
        """
        Returns the data of monitor devices for data calculation.
        """
        return polarisation_filter(self.flippers_data, self.time, polarisation)

    @property
    def owner(self) -> Person:
        """
        Returns the owner of file for orso file.
        """
        user = {}
        users_str = self.metadata['Experiment information']['Exp_users']
        if '{' in users_str and '}' in users_str:
            user = ast.literal_eval(users_str)[0]
        else:
            user['name'] = users_str.split(',')[0]
        return Person(name=user.get('name'), contact=user.get('email'))

    @property
    def experiment(self) -> Experiment:
        """
        Returns the experiment for orso file.
        """
        instrument_setup = {key.split('_')[1]: value for key, value in self.metadata['Instrument setup'].items()}
        return Experiment(title=self.metadata['Experiment information']['Exp_title'],
                          instrument=instrument_setup['instrument'],
                          probe='neutron',
                          doi=instrument_setup['doi'],
                          start_date=datetime.strptime(self.metadata['General']['Date'],
                                                       "%Y-%m-%d %H:%M:%S"),
                          proposalID=str(self.metadata['Experiment information']['Exp_proposal']))

    @property
    def sample(self) -> Sample:
        """
        Returns the experiment for orso file.
        """
        sample = {key.split('_')[1]: value
                  for key, value in self.metadata['Sample and alignment'].items()}
        return Sample(name=sample['samplename'], category=sample['category'],
                      composition=sample['composition'], description=sample['description'],
                      size=ValueVector(x=sample['length'], y=sample['height'], z=sample['thickness'], unit="mm")
                      )

    def slit_configuration(self) -> dict:
        values = self.metadata['Device positions and sample environment state']
        get_distance = lambda slit_name: values.get(f'd_{slit_name}_value').split()
        get_size = lambda slit_name: (values.get(f'{slit_name}_value').split()[2],
                                      values.get(f'{slit_name}_value').split()[-1])
        slit_config = [(*get_distance(slit), *get_size(slit)) for slit in SLIT_DEVICES]
        slit_configuration = {
            "divergence_distance": Value(*slit_config[0][:2]),
            "divergence_opening": Value(*slit_config[0][2:]),
            "size_distance": Value(*slit_config[1][:2]),
            "size_opening": Value(*slit_config[1][2:]),
        }
        return slit_configuration

    def instrument_settings(self, polarisation: Polarization) -> InstrumentSettings:
        """
        Returns the experiment for orso file.
        """
        theta_angles = self.dataset[INCIDENT_ANGLE_AXIS].to_numpy()
        unit = self.scanfile.header_units[self.scanfile.header.index(INCIDENT_ANGLE_AXIS)]
        incident_angle = ValueRange(theta_angles.min(), theta_angles.max(), unit)
        wavelength = self.metadata['Device positions and sample environment state']['wavelength_value']
        wavelength = float(wavelength.split()[0]), wavelength.split()[1]

        instrument_settings = InstrumentSettings(incident_angle=incident_angle,
                                                 wavelength=Value(*wavelength),
                                                 polarization=polarisation)
        instrument_settings.slit_configuration = self.slit_configuration()
        instrument_settings.incident_intensity = INTENSITY
        instrument_settings.incident_polarization = POLARISATION
        return instrument_settings

    def measurement(self, polarisation: Polarization) -> Measurement:
        """
        Returns the experiment for orso file.
        """
        return Measurement(instrument_settings=self.instrument_settings(polarisation),
                           data_files=self.metadata['General']['filepath'])


def get_data(file_path: str) -> Metadata:
    if file_path.endswith('.nxs'):
        return NexusFile(file_path)
    elif file_path.endswith('.dat'):
        return ScanDataFile(file_path)
    else:
        raise ValueError("Unknown file type")


def create_orso(data: Metadata, detector: str, region=None):
    res = []
    if detector not in data.detectors_list:
        raise ValueError('Wrong detector name')
    if detector == "2Ddata" and region is None:
        raise ValueError('region chould be set')

    reduction = Reduction(
        software=Software(name="converttonarziss.py", version=__version__, platform=sys.platform),
        corrections=["Calculate Q from Angle"],
    )

    columns = [
        Column(name="Q", unit="1/Angstrom"),
        Column(name="I", unit="1/monitor"),
        ErrorColumn(error_of="I"),
    ]
    owner = data.owner
    experiment = data.experiment
    sample = data.sample

    for polarisation in data.polarisation:
        measurement = data.measurement(polarisation)
        data_source = DataSource(owner, experiment, sample, measurement)
        theta = data.get_dataset('theta', polarisation)
        counts = data.get_dataset(detector, polarisation)
        if detector == "2Ddata":
            counts = counts[:, region[0]:region[1] + 1, region[2]:region[3] + 1]
            counts = np.sum(counts, axis=(1, 2))
            counts = counts / ((region[1] - region[0] + 1) * (region[3] - region[2] + 1))

        data_source.measurement.instrument_settings.incident_intensity = Value(counts.max()/np.mean(data.monitor),
                                                                               "1/monitor")
        monitor = data.get_dataset_monitor(polarisation)
        Q = 4 * np.pi / measurement.instrument_settings.wavelength.magnitude * np.sin(theta * np.pi / 180.0)
        I = counts / monitor
        dI = np.sqrt(counts) / monitor
        header = Orso(data_source, reduction, columns)
        res.append(OrsoDataset(header, np.array([Q, I, dI]).T))

    output_name = os.path.splitext(os.path.basename(data.file_path))[0]
    save_orso(res, f"NOB_reflectivity_{output_name}.ort")


def main():
    parser = argparse.ArgumentParser(description="Process detector data.")

    parser.add_argument("filename", help="Path to the input data file (e.g., .npy)")
    parser.add_argument("detector", help="Name of detector or ROI. For nexus file 2Ddata "
                                         "coresponding to 2D picture. Use --region to set ROI in this case.")
    parser.add_argument("--region", type=int, nargs=4, metavar=('y1', 'y2', 'x1', 'x2'),
                        help="ROI region for 2Ddata detector: y1 y2 x1 y1")

    args = parser.parse_args()
    data = get_data(args.filename)
    create_orso(data, args.detector, args.region)


if __name__ == "__main__":
    main()

