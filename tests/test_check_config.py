import pytest
from unittest.mock import Mock
from converter.check_config import check_config
from converter.datatypes import (
    CorrectionParameters,
    DataSourceConfig,
    BackgroundConfig,
    BackgroundTypeCorrection,
    NormalisationConfig,
    ReductionConfig
)


class MockMetadata:
    def __init__(self, detectors_list=None):
        self._detectors_list = detectors_list or ["detector1", "detector2"]

    @property
    def detectors_list(self):
        return self._detectors_list


def test_check_config_valid():
    parameters = CorrectionParameters(
        data_source=DataSourceConfig(detector="detector1", region=None),
        background=BackgroundConfig(use_correction=False),
        reduction=ReductionConfig(),
        normalisation=NormalisationConfig()
    )
    data = MockMetadata(detectors_list=["detector1", "detector2"])

    check_config(parameters, data)


def test_check_config_wrong_detector():
    parameters = CorrectionParameters(
        data_source=DataSourceConfig(detector="wrong_detector", region=None),
        background=BackgroundConfig(use_correction=False),
        reduction=ReductionConfig(),
        normalisation=NormalisationConfig()
    )
    data = MockMetadata(detectors_list=["detector1", "detector2"])

    with pytest.raises(ValueError, match="Wrong detector name"):
        check_config(parameters, data)


def test_check_config_2ddata_without_region():
    parameters = CorrectionParameters(
        data_source=DataSourceConfig(detector="2Ddata", region=None),
        background=BackgroundConfig(use_correction=False),
        reduction=ReductionConfig(),
        normalisation=NormalisationConfig()
    )
    data = MockMetadata(detectors_list=["detector1", "2Ddata"])

    with pytest.raises(ValueError, match="Region should be set"):
        check_config(parameters, data)


def test_check_config_psdRegion_with_2ddata():
    parameters = CorrectionParameters(
        data_source=DataSourceConfig(detector="2Ddata", region=(0, 10, 0, 10)),
        background=BackgroundConfig(
            use_correction=True,
            correction_type=BackgroundTypeCorrection.psdRegion,
            region=(0, 5, 0, 5)
        ),
        reduction=ReductionConfig(),
        normalisation=NormalisationConfig()
    )
    data = MockMetadata(detectors_list=["detector1", "2Ddata"])

    with pytest.raises(ValueError, match="The background correction request 2Ddata detector name"):
        check_config(parameters, data)


def test_check_config_psdRegion_without_background_region():
    parameters = CorrectionParameters(
        data_source=DataSourceConfig(detector="detector1", region=None),
        background=BackgroundConfig(
            use_correction=True,
            correction_type=BackgroundTypeCorrection.psdRegion,
            region=None
        ),
        reduction=ReductionConfig(),
        normalisation=NormalisationConfig()
    )
    data = MockMetadata(detectors_list=["detector1", "detector2"])

    with pytest.raises(ValueError, match="Background region should be set"):
        check_config(parameters, data)
