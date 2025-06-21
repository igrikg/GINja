import sys
from typing import List, Tuple
from dataclasses import asdict

import numpy as np
from orsopy.fileio import (Measurement, InstrumentSettings,
                           Sample, Person, Experiment, Polarization, Reduction,
                           Software, Column, ErrorColumn, DataSource, Orso, OrsoDataset, ValueVector, ValueRange, Value,
                           save_orso)

from .config import WAVELENGTH_RESOLUTION, VERSION
from .datatypes import DataSet, CorrectionParameters, DataSetMetadata, MeasurementData, AdsorptionTypeCorrection, \
    IntensityTypeCorrection, BackgroundTypeCorrection

from .utils import convert_dataclass


def get_header_orso(header: DataSetMetadata) -> Tuple[Person, Experiment, Sample]:
    owner = convert_dataclass(header.owner, Person)
    experiment = convert_dataclass(header.experiment, Experiment)
    sample = convert_dataclass(header.sample, Sample)
    sample.size = ValueVector(x=header.sample.length, y=header.sample.height,
                              z=header.sample.thickness, unit=header.sample.units)
    return owner, experiment, sample


def get_measurement_orso(measurement: MeasurementData) -> Measurement:
    is_data = measurement.instrument_settings
    instrument_settings =InstrumentSettings(
        incident_angle=ValueRange(is_data.incident_angle[0],
                                  is_data.incident_angle[0],
                                  unit=is_data.angle_unit),
        wavelength=Value(is_data.wavelength, unit=is_data.wavelength_unit),
        polarization=Polarization(is_data.polarization.value),
    )
    instrument_settings.slit_configuration = {key: Value(val, unit=is_data.slit_configuration.units)
                                              for key, val in asdict(is_data.slit_configuration).items()
                                              if key != 'units'}
    instrument_settings.polarization_efficiency = {key: Value(val) for key, val in
                                                   asdict(is_data.polarization_efficiency).items()}
    meas = asdict(measurement)
    meas['instrument_settings'] = instrument_settings
    return Measurement(**meas)


class OrsoData:
    def __init__(self, data: List[DataSet], parameters: CorrectionParameters):
        self.__data = data
        self.__parameters = parameters

    @property
    def reduction(self):
        parameters = self.__parameters
        corrections = [f"Collect intensity from {parameters.data_source.detector}" +
                       (f" from region {str(parameters.data_source.region)}"
                        if parameters.data_source.region is not None else "")]
        if parameters.reduction.foot_print_correction:
            corrections.append("Made foot print correction with trapezoid beam")
        if parameters.reduction.polarisation_correction:
            corrections.append("Made polarisation correction")
        if parameters.reduction.absorption_correction:
            if parameters.reduction.mu_type == AdsorptionTypeCorrection.constValue:
                mu = f"mu = {str(parameters.reduction.mu_value)}"
            elif parameters.reduction.mu_type == AdsorptionTypeCorrection.typical:
                mu = f"mu({parameters.reduction.mu_enum.name}) = {str(parameters.reduction.mu_enum.value)}"
            else:
                mu = ""
            corrections.append(f"Made absorption correction with {mu}")
        #normalisation
        if parameters.normalisation.time:
            corrections.append("Made time normalisation")
        if parameters.normalisation.monitor:
            corrections.append("Made monitor counts normalisation")
        if parameters.normalisation.intensity_norm:
            in_norm = ""
            if parameters.normalisation.intensity_norm_type == IntensityTypeCorrection.constValue:
                in_norm = f"constant value {parameters.normalisation.intensity_value}"
            if parameters.normalisation.intensity_norm_type == IntensityTypeCorrection.maxValue:
                in_norm = f"maximum intensity point in current dataset"
            if parameters.normalisation.intensity_norm_type == IntensityTypeCorrection.maxValueGlobal:
                in_norm = f"maximum intensity point of all datasets"
            if parameters.normalisation.intensity_norm_type == IntensityTypeCorrection.psdRegion:
                in_norm = (f"from special point ({str(parameters.normalisation.intensity_point_number)})"
                           f" in region of detector {str(parameters.normalisation.intensity_region)}")
            corrections.append(f"Made intensity normalisation by {in_norm}")
        if parameters.background.use_correction:
            bk_norm = ""
            if parameters.background.correction_type == BackgroundTypeCorrection.constValue:
                bk_norm = f"with constant value {parameters.background.value}"
            if parameters.background.correction_type == BackgroundTypeCorrection.extraFile:
                bk_norm = f"from file {parameters.background.file}"
            if parameters.background.correction_type == BackgroundTypeCorrection.psdRegion:
                bk_norm = f"from PSD in region {parameters.background.region}"
            corrections.append(f"Made background correction {bk_norm}")
        corrections.append("Calculate Q from Angle")
        corrections.append(f"Calculate dQ from Slit parameters and delta lambda / lambda = "
                           f"{round(WAVELENGTH_RESOLUTION*100, 1)}%")
        corrections.append("Calculate dR like Poisson distribution")
        return Reduction(
            software=Software(name="Ginja.py", version=VERSION, platform=sys.platform),
            call=parameters.program_call,
            corrections=corrections
        )

    @property
    def columns(self):
        return [
            Column(name="Q", unit="1/Angstrom"),
            ErrorColumn(error_of="Q"),
            Column(name="R"),
            ErrorColumn(error_of="R"),
        ]

    @property
    def orso_dataset(self):
        res = []
        for dataset in self.__data:
            data_source = DataSource(
                *get_header_orso(dataset.header),
                get_measurement_orso(dataset.measurement))
            header = Orso(data_source, self.reduction, self.columns)
            res.append(OrsoDataset(header, np.array([dataset.result.Q,dataset.result.dQ,
                                                     dataset.result.R, dataset.result.dR]).T))
        return res

    def save(self, filename):
        save_orso(self.orso_dataset, f"{filename}.ort")








