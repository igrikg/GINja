from .datatypes import CorrectionParameters, BackgroundTypeCorrection
from .iofile import Metadata


def check_config(parameters: CorrectionParameters, data: Metadata):
    if parameters.data_source.detector not in data.detectors_list:
        raise ValueError('Wrong detector name')
    if parameters.data_source.detector == "2Ddata" and parameters.data_source.region is None:
        raise ValueError('Region should be set')

    if parameters.background.use_correction:
        if parameters.background.correction_type == BackgroundTypeCorrection.psdRegion:
            if parameters.data_source.detector == "2Ddata":
                raise ValueError('The background correction request 2Ddata detector name')
            if parameters.background.region is None:
                raise ValueError('Background region should be set')
