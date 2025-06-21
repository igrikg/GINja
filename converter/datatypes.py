from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Union, Iterable, List, Tuple, Literal
from numpy.typing import NDArray

from .config import FACILITY, DEFAULT_AFFILIATION, DEFAULT_DETECTOR


class MuDataEnum(Enum):
    """Mu for typical substrates"""
    glass = 0.0001667
    Si = 0.0000556
    SiO2 = 0.0000278
    Al2O3 = 0.0000278


class AdsorptionTypeCorrection(Enum):
    constValue = "constValue"
    typical = "typical"


class BackgroundTypeCorrection(Enum):
    constValue = "constValue"
    psdRegion = "psdRegion"
    extraFile = "extraFile"


class IntensityTypeCorrection(Enum):
    constValue = "constValue"
    maxValue = "maxValueDataset"
    maxValueGlobal = "maxValueGlobal"
    psdRegion = "psdRegion"


class PolarizationEnum(str, Enum):
    """Polarization state enumeration"""
    unpolarized = "unpolarized"
    po = "po"
    mo = "mo"
    op = "op"
    om = "om"
    mm = "mm"
    mp = "mp"
    pm = "pm"
    pp = "pp"


@dataclass
class SlitData:
    slit1_width: float
    slit2_width: float
    slit1_position: float
    slit2_position: float
    units: str = 'mm'


@dataclass
class PolarisationEfficiencyData:
    polarizer: float = 1.0
    analyser: float = 1.0
    spin_flipper_1: float = 1.0
    spin_flipper_2: float = 1.0


@dataclass
class PersonData:
    name: str
    affiliation: str = DEFAULT_AFFILIATION
    contact: Union[str, None] = None


@dataclass
class InstrumentSettingsData:
    incident_angle: Tuple[float, float]
    angle_unit: str
    wavelength: float
    slit_configuration: SlitData
    wavelength_unit: str = 'A'
    incident_intensity: Union[float, None] = None
    polarization: PolarizationEnum = PolarizationEnum.unpolarized
    configuration: Union[str, None] = None
    polarization_efficiency: PolarisationEfficiencyData = field(default_factory=PolarisationEfficiencyData)


@dataclass
class MeasurementData:
    instrument_settings: InstrumentSettingsData
    data_files: Union[List[str], str]
    additional_files: Union[List[str], None] = None
    scheme: str = "angle-dispersive"


@dataclass
class SampleData:
    """Sample parameters"""
    name: str
    category: Union[str, None] = None
    composition: Union[str, None] = None
    description: Union[str, None] = None
    environment: Union[List[str], None] = None
    length: float = 0
    thickness: float = 0
    height: float = 0
    units: str = 'mm'


@dataclass
class ExperimentData:
    title: str
    instrument: str
    start_date: datetime
    proposalID: Union[str, None] = None
    doi: Union[str, None] = None
    probe: Literal["neutron", "x-ray"] = "neutron"
    facility: str = FACILITY


@dataclass
class NormalisationConfig:
    time: bool = True
    monitor: bool = True
    #detector_efficiency: bool = False
    intensity_norm: bool = True
    intensity_norm_type: IntensityTypeCorrection = IntensityTypeCorrection.constValue
    intensity_value: float = 1.0
    intensity_point_number: int = 1  # off position
    intensity_region: Union[Iterable, None] = None


@dataclass
class ReductionConfig:
    foot_print_correction: bool = True
    absorption_correction: bool = True
    polarisation_correction: bool = False
    mu_type: AdsorptionTypeCorrection = AdsorptionTypeCorrection.constValue
    mu_enum: MuDataEnum = MuDataEnum.glass
    mu_value: float = 0


@dataclass
class BackgroundConfig:
    use_correction: bool = True
    correction_type: BackgroundTypeCorrection = BackgroundTypeCorrection.constValue
    file: Union[str, None] = None
    value: float = 1e-12
    region: Union[Iterable, None] = None


@dataclass
class DataSourceConfig:
    detector: str = DEFAULT_DETECTOR
    region: Union[Iterable, None] = None


@dataclass
class CorrectionParameters:
    """Correction parameters"""
    data_source: DataSourceConfig
    normalisation: NormalisationConfig = field(default_factory=NormalisationConfig)
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    reduction: ReductionConfig = field(default_factory=ReductionConfig)
    program_call: str = ""


@dataclass
class DataSetMetadata:
    owner: PersonData
    experiment: ExperimentData
    sample: SampleData


@dataclass
class DataSetOutput:
    Q: Union[NDArray | None] = None
    dQ: Union[NDArray | None] = None
    R: Union[NDArray | None] = None
    dR: Union[NDArray | None] = None


@dataclass
class DataSet:
    header: DataSetMetadata
    measurement: MeasurementData
    theta: NDArray
    time: NDArray
    monitor: NDArray
    counts: NDArray
    e_counts: NDArray
    background: NDArray
    e_background: NDArray
    result: DataSetOutput

