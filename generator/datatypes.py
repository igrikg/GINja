from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Union

from numpy.typing import NDArray
from orsopy.fileio import Polarization

Q2M = 1 / 0.0218


class EvaluationState(Enum):
    accepted = "Accepted"
    rejected = "Rejected"
    special = "Note"


@dataclass
class ConfigReportInput:
    M_ref: float = 6.2  # location for reference reflectivity at high m
    R_ref: float = 0.6  # reflectivity at reference location
    R_div_max: float = 0.1  # maximum deviation from theoretical curve

    M_max: float = 6.2  # m-value from specification (theoretical curve drop)

    alpha_spec: float = 0.075  # alpha for theoretical curve
    alpha_max: float = 0.075  # limit for measured alpha from specification
    fit_alfa: bool = True  # evaluat alpha by fitting, not calculation

    P_min: float = 0.95  # minimum polarization over Q-range

    Q_Pstart: float = 0.022 #0.022  # evaluation of reflectivity starts at this q-value, use m=1 to ignore footprint issues in irrelevant parts
    Q_Pend: float = M_max / Q2M


@dataclass
class MainReportInput:
    owner: str
    instrument: str
    proposal_id: str
    start_date: str
    proposal_name: str
    sample_name: str
    sample_size: Iterable[float]
    filename: str
    correction: Iterable[str]


@dataclass
class SummaryReportInput:
    evaluation: EvaluationState
    alpha: float = 0
    R_m_ref: float = 1
    R_div_max: float = 1

    Pmin: float = 1
    Pavg: float = 1
    ref_in_spec: bool = True
    pol_in_spec: bool = False
    scale: float = 0
    use_polarisation: bool = True


@dataclass
class DataReportInput:
    x: NDArray
    y: NDArray
    dx: NDArray
    dy: NDArray
    label: str = ""
    color: Union[str | None] = None


@dataclass
class ReportInput:
    main: MainReportInput
    summary: SummaryReportInput
    data: List[DataReportInput]
    polarisation: DataReportInput
    config: ConfigReportInput
    polar_pos: dict[Polarization:int]
