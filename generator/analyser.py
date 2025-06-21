from pathlib import Path
from typing import List, Union

import numpy as np
from orsopy import fileio
from orsopy.fileio import Polarization
from scipy.optimize import curve_fit

from .datatypes import (ReportInput, DataReportInput, ConfigReportInput, MainReportInput, Q2M,
                        EvaluationState, SummaryReportInput)
from .utils import ideal_reflectivity


class AnalyserOrso:
    def __init__(self, file_name, config: ConfigReportInput):
        self.__file_name = file_name
        self.__config = config
        self.file_data = fileio.load_orso(file_name)
        self.__polar_position: dict[Polarization: int] = {}
        self.__data_list: List[DataReportInput] = []
        self.__polarisation: Union[DataReportInput | None] = None

    @property
    def main(self):
        return MainReportInput(sample_name=self.file_data[0].info.data_source.sample.name,
                               instrument=self.file_data[0].info.data_source.experiment.instrument,
                               proposal_id=self.file_data[0].info.data_source.experiment.proposalID,
                               proposal_name=self.file_data[0].info.data_source.experiment.title,
                               start_date=self.file_data[0].info.data_source.experiment.start_date.strftime("%Y-%m-%d"),
                               owner=self.file_data[0].info.data_source.owner.name,
                               sample_size=[self.file_data[0].info.data_source.sample.size.x,
                                            self.file_data[0].info.data_source.sample.size.y,
                                            self.file_data[0].info.data_source.sample.size.z],
                               filename=Path(self.__file_name).name,
                               correction=self.file_data[0].info.reduction.corrections
                               )

    @staticmethod
    def get_scale_and_alpha(data: DataReportInput, config: ConfigReportInput):
        def ideal_reflectivity_m(m, scale, alpha):
            return ideal_reflectivity(m, scale, alpha, config.M_max)

        Q, R, dR = data.x, data.y, data.dy
        if config.fit_alfa:
            fit_range = (Q > config.Q_Pstart) & (Q <= ((config.M_max + 0.05) / Q2M))
            p0 = [1.0, config.alpha_spec]
            res = curve_fit(ideal_reflectivity_m, xdata=Q[fit_range] * Q2M,
                            ydata=R[fit_range], sigma=dR[fit_range], absolute_sigma=True,
                            p0=p0, method="lm", full_output=True)
            scale, alpha = res[0]
        else:
            c_range = (Q > (0.5 / Q2M)) & (Q <= (1.0 / Q2M))
            a_range = (Q > (1.0 / Q2M)) & (Q <= ((config.M_max + 0.05) / Q2M))
            scale = R[c_range].mean()
            alpha = 2.0 / (config.M_max - 1) - 2 * np.trapezoid(R[a_range], Q[a_range] * Q2M) / (
                    scale * (config.M_max - 1) ** 2
            )
        return scale, alpha

    @staticmethod
    def get_refl_spec(data: DataReportInput, config: ConfigReportInput):
        Q, R = data.x, data.y
        q_range = (Q > config.Q_Pstart) & (Q <= config.Q_Pend)
        ref = ideal_reflectivity(Q * Q2M, 1.0, config.alpha_spec, config.M_max)
        R_div_max = (1.0 - R[q_range] / ref[q_range]).max()
        r_filtr = R[(Q > (config.M_ref / Q2M))]
        R_m_ref = float(R[(Q > (config.M_ref / Q2M))][0]) if r_filtr.size > 0 else 0
        return R_m_ref, R_div_max

    def __get_refl_data(self, polarisation: Polarization) -> DataReportInput:
        index_R = max(self.polar_pos.get(polarisation, -1),
                      self.polar_pos.get(Polarization.unpolarized, -1))
        return self.dataset[index_R]

    def __update_dataset_list(self):
        self.__data_list = []
        labels = {Polarization.po: "spin-up",
                  Polarization.mo: "spin-down"}
        for i, dataset in enumerate(self.file_data):
            self.__data_list.append(
                DataReportInput(x=dataset.data[:, 0], y=dataset.data[:, 2],
                                dx=np.zeros_like(dataset.data[:, 1]), dy=dataset.data[:, 3],
                                label=labels.get(dataset.info.data_source.measurement.instrument_settings.polarization)
                                )
            )
            self.__polar_position[dataset.info.data_source.measurement.instrument_settings.polarization] = i

    @property
    def dataset(self):
        if not self.__data_list:
            self.__update_dataset_list()
        return self.__data_list

    @property
    def polar_pos(self):
        if not self.__polar_position:
            self.__update_dataset_list()
        return self.__polar_position

    @property
    def summary(self):
        data_Rup = self.__get_refl_data(Polarization.po)
        R_m_ref, R_div_max = AnalyserOrso.get_refl_spec(data_Rup, self.config)
        scale, alpha = AnalyserOrso.get_scale_and_alpha(data_Rup, self.config)

        ref_in_spec = (
                alpha < self.config.alpha_max
                and R_m_ref > self.config.R_ref
                and R_div_max < self.config.R_div_max
        )
        Q, P = self.polarisation.x, self.polarisation.y
        q_range = (Q >= self.config.Q_Pstart) & (Q <= self.config.Q_Pend)
        Pmin = float(np.nanmin(P[q_range]))
        Pavg = float(np.nanmean(P[q_range]))
        pol_in_spec = Pmin >= self.config.P_min
        evaluation = EvaluationState.accepted if ref_in_spec and pol_in_spec else EvaluationState.rejected
        return SummaryReportInput(
            evaluation=evaluation,
            use_polarisation=len(self.polar_pos.keys()) > 1,
            scale=scale,
            alpha=alpha,
            R_m_ref=R_m_ref,
            R_div_max=R_div_max,
            ref_in_spec=ref_in_spec,
            pol_in_spec=pol_in_spec,
            Pmin=Pmin,
            Pavg=Pavg,
        )

    @property
    def config(self):
        return self.__config

    @property
    def polarisation(self) -> DataReportInput:
        if self.__polarisation is not None:
            return self.__polarisation

        data_p = self.__get_refl_data(Polarization.po)
        data_m = self.__get_refl_data(Polarization.mo)

        R_p, s_p = data_p.y, data_p.dy
        R_m, s_m = data_m.y, data_m.dy

        P = (R_p - R_m) / (R_p + R_m)

        # Calculate error
        denominator = (R_p + R_m) ** 2
        P_err = np.sqrt(
            (2 * R_m * s_p / denominator) ** 2 +
            (2 * R_p * s_m / denominator) ** 2
        )

        self.__polarisation = DataReportInput(
            x=self.file_data[0].data[:, 0], y=P,
            dx=np.zeros_like(self.file_data[0].data[:, 1]), dy=P_err,
            label="polarization",
            color="green"
        )
        return self.__polarisation

    @property
    def result(self) -> ReportInput:
        return ReportInput(main=self.main,
                           summary=self.summary,
                           data=self.dataset,
                           polarisation=self.polarisation,
                           config=self.config,
                           polar_pos=self.polar_pos)
