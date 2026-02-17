from pathlib import Path
from typing import List

import numpy as np
from .calulation import q_with_resolution_from_slits
from .correction import footprint_correction_two_slits, absorption_correction
from .datatypes import (CorrectionParameters, BackgroundTypeCorrection, DataSet, DataSetMetadata,
                        DataSetOutput, AdsorptionTypeCorrection, IntensityTypeCorrection)
from .iofile import Metadata
from .config import WAVELENGTH_RESOLUTION

from .orso_convert import OrsoData
from .utils import safety_div


class DataReduction:
    def __init__(self, data: Metadata, parameters: CorrectionParameters):
        self.__parameters: CorrectionParameters = parameters
        self.__data: Metadata = data
        self.data_list: List[DataSet] = self.__create_data_list()

    def __get_detector_data(self, polarisation):

        def extract_region_mean(array, roi):
            y_min, y_max, x_min, x_max = roi
            sub_counts = array[:, y_min:y_max + 1, x_min:x_max + 1]
            array = np.sum(sub_counts, axis=(1, 2))
            pixel_num = (y_max - y_min + 1) * (x_max - x_min + 1)
            return array / pixel_num, np.sqrt(array) / pixel_num

        def regions_overlap(region1, region2):
            y1_min, y1_max, x1_min, x1_max = region1
            y2_min, y2_max, x2_min, x2_max = region2
            return not (y2_max < y1_min or y2_min > y1_max or x2_max < x1_min or x2_min > x1_max)

        detector = self.__parameters.data_source.detector
        region = self.__parameters.data_source.region
        region_background = self.__parameters.background.region
        counts = self.__data.get_dataset(detector, polarisation)
        background = np.zeros_like(counts)
        background_error = np.zeros_like(counts)
        if detector != "2Ddata":
            signal = counts
            signal_error = np.sqrt(counts)
        else:
            signal, signal_error = extract_region_mean(counts, region)
            if (self.__parameters.background.use_correction and
                    self.__parameters.background.correction_type == BackgroundTypeCorrection.psdRegion):
                if regions_overlap(region, region_background):
                    # Remove the overlapping part from the background
                    mask = np.ones_like(counts[0], dtype=bool)
                    sy0, sy1, sx0, sx1 = region
                    mask[sy0:sy1 + 1, sx0:sx1 + 1] = False

                    by0, by1, bx0, bx1 = region_background
                    masked_counts = counts[:, by0:by1 + 1, bx0:bx1 + 1]
                    masked_mask = mask[by0:by1 + 1, bx0:bx1 + 1]

                    background = np.array([
                        np.sum(frame[masked_mask]) / np.sum(masked_mask)
                        for frame in masked_counts
                    ])
                    background_error = np.array([
                        np.sqrt(np.sum(frame[masked_mask])) / np.sum(masked_mask)
                        for frame in masked_counts
                    ])
                else:
                    background, background_error = extract_region_mean(counts, region_background)
        return signal, background, signal_error, background_error

    def __create_data_list(self) -> List[DataSet]:
        result = []
        header = DataSetMetadata(owner=self.__data.owner,
                                 experiment=self.__data.experiment,
                                 sample=self.__data.sample
                                 )
        for polarisation in self.__data.polarisation:
            measurement = self.__data.measurement(polarisation)
            theta = self.__data.get_dataset('theta', polarisation)
            counts, background, e_counts, e_background = self.__get_detector_data(polarisation)
            monitor = self.__data.get_dataset_monitor(polarisation)
            time = self.__data.get_dataset_time(polarisation)
            result.append(
                DataSet(header=header,
                        measurement=measurement,
                        counts=counts,
                        theta=theta,
                        time=time,
                        monitor=monitor,
                        background=background,
                        result=DataSetOutput(),
                        e_counts=e_counts,
                        e_background=e_background
                        )
            )
        return result

    def __correction(self, dataset: DataSet):
        norm_coefficient = np.ones_like(dataset.counts)
        if self.__parameters.reduction.foot_print_correction:
            norm_coefficient *= footprint_correction_two_slits(dataset.theta,
                                                               dataset.measurement.instrument_settings.slit_configuration,
                                                               dataset.header.sample.length)
        if self.__parameters.reduction.absorption_correction:
            if self.__parameters.reduction.mu_type == AdsorptionTypeCorrection.constValue:
                mu = self.__parameters.reduction.mu_value
            elif self.__parameters.reduction.mu_type == AdsorptionTypeCorrection.typical:
                mu = self.__parameters.reduction.mu_enum.value
            else:
                mu = 0
            norm_coefficient *= absorption_correction(dataset.theta,
                                                      dataset.measurement.instrument_settings.wavelength,
                                                      mu, dataset.header.sample)
        if self.__parameters.reduction.polarisation_correction:
            raise NotImplementedError()
        return norm_coefficient

    def __normalisation(self, dataset: DataSet):
        norm_coefficient = np.ones_like(dataset.counts)
        if self.__parameters.normalisation.monitor:
            norm_coefficient = safety_div(norm_coefficient, dataset.monitor)
        if self.__parameters.normalisation.time:
            norm_coefficient = safety_div(norm_coefficient, dataset.time)
        return norm_coefficient

    def __background_correction(self, dataset: DataSet, norm_coefficient):
        if self.__parameters.background.use_correction:
            if self.__parameters.background.correction_type == BackgroundTypeCorrection.constValue:
                dataset.result.R -= self.__parameters.background.value
            if self.__parameters.background.correction_type == BackgroundTypeCorrection.extraFile:
                raise NotImplementedError
            if self.__parameters.background.correction_type == BackgroundTypeCorrection.psdRegion:
                dataset.result.R -= dataset.background * norm_coefficient
                dataset.result.dR = np.sqrt(dataset.result.dR ** 2 + (dataset.e_background * norm_coefficient) ** 2)

    def __intensity_correction(self, dataset: DataSet):
        if self.__parameters.normalisation.intensity_norm:
            if self.__parameters.normalisation.intensity_norm_type == IntensityTypeCorrection.constValue:
                dataset.result.R /= self.__parameters.normalisation.intensity_value
                dataset.result.dR /= self.__parameters.normalisation.intensity_value
            if self.__parameters.normalisation.intensity_norm_type == IntensityTypeCorrection.maxValue:
                max_value = np.max(dataset.result.R)
                dataset.result.R /= max_value
                dataset.result.dR /= max_value

    def __calculate(self):
        for dataset in self.data_list:
            (dataset.result.Q,
             dataset.result.dQ) = q_with_resolution_from_slits(dataset.theta,
                                                               dataset.measurement.instrument_settings.wavelength,
                                                               dataset.measurement.instrument_settings.slit_configuration,
                                                               dlam_rel=WAVELENGTH_RESOLUTION)

            corr_coefficient = self.__correction(dataset)
            norm_coefficient = self.__normalisation(dataset)
            dataset.result.R = dataset.counts * corr_coefficient * norm_coefficient
            dataset.result.dR = dataset.e_counts * corr_coefficient * norm_coefficient
            self.__background_correction(dataset, norm_coefficient)
            self.__intensity_correction(dataset)

        if self.__parameters.normalisation.intensity_norm_type == IntensityTypeCorrection.maxValueGlobal:
            max_value = np.max([np.max(dataset.result.R) for dataset in self.data_list])
            for dataset in self.data_list:
                dataset.result.R /= max_value
                dataset.result.dR /= max_value

        if self.__parameters.normalisation.intensity_norm_type == IntensityTypeCorrection.psdRegion:
            raise NotImplementedError("IntensityTypeCorrection.psdRegion is not implemented yet")

    @property
    def result(self) -> List[DataSet]:
        self.__calculate()
        return self.data_list

    def create_orso(self, filename=None, path=None, folder_input_file=False):
        if filename is None:
            filename = Path(self.__data.file_path).stem
        if path is not None:
            filename = Path(path) / filename
        if path is None and folder_input_file:
            filename = Path(self.__data.file_path).parent.name / Path(filename)

        OrsoData(self.result, self.__parameters).save(filename)
