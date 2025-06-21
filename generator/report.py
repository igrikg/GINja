import textwrap
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt, image as mpimg

from orsopy.fileio import Polarization

from .datatypes import ReportInput, Q2M
from .utils import ideal_reflectivity

E_LABEL = {True: "in specification", False: "out of specification"}


class ReportGenerator:
    def __init__(self, report_info: ReportInput):
        self.gs = None
        self.fig = None
        self.result = report_info
        self.setup_page()
        self.draw_evaluation()
        self.plot_reflectivity()
        self.plot_corrected_reflectivity()
        if self.result.summary.use_polarisation:
            self.plot_polarization()
        self.draw_parameters()

    def show(self):
        plt.show()

    def savepdf(self, file_name):
        if file_name is None:
            file_name=f"{Path(self.result.main.filename).stem}.pdf"
        plt.savefig(file_name, dpi=150)

    def get_figure(self):
        return self.fig

    def setup_page(self):
        self.fig = plt.figure(figsize=(8.2677, 11.6929), dpi=80, constrained_layout=False)
        self.fig.suptitle(
            "Budapest Neutron Centre",
            fontsize=14,
            fontweight="bold",
            ha='left',
            color="#1e3769",
            x=0.04,
            y=0.97
        )

        self.fig.text(
            0.04, 0.935,
            f"Reflectometry report for sample \"{self.result.main.sample_name}\"",
            fontsize=12, fontweight="bold",
            ha='left',
            color="#156da2",
        )

        # Define the gridspec (already done)
        self.gs = self.fig.add_gridspec(
            nrows=20, ncols=10, left=0.02, right=0.92, top=0.88, bottom=0.05, hspace=1.5, wspace=0.8
        )


        # Add header image (top)
        header_img = mpimg.imread("generator/header.png")
        header_ax = self.fig.add_axes((0.0, 0.90, 1.0, 0.1))  # [left, bottom, width, height]
        header_ax.imshow(header_img)
        header_ax.axis("off")

        # Add footer image (bottom)
        footer_img = mpimg.imread("generator/footer.png")
        footer_ax = self.fig.add_axes((0.0, 0.001, 1.0, 0.05))  # [left, bottom, width, height]
        footer_ax.imshow(footer_img)
        footer_ax.axis("off")

    def draw_evaluation(self):
        ax = self.fig.add_subplot(self.gs[0:3, :])
        ax.set_facecolor((0, 0, 0, 0))
        ax.axis("off")
        ax.text(20, 0, "Measurement Report:", horizontalalignment="center", fontdict={"fontweight": "bold"})
        ax.text(0, -20, "Instrument:")
        ax.text(0, -35, "Experiment:")
        ax.text(0, -50, "Experiment ID:")
        ax.text(0, -65, "Date Measured:")
        ax.text(0, -80, "User name:")
        ax.text(20, -20, self.result.main.instrument)
        ax.text(20, -35, self.result.main.proposal_name)
        ax.text(20, -50, self.result.main.proposal_id)
        ax.text(20, -65, self.result.main.start_date)
        ax.text(20, -80, self.result.main.owner)

        ax.text(60, 0, "Analysis Results:", horizontalalignment="center", fontdict={"fontweight": "bold"})
        ax.text(45, -20, "Reflectivity:")
        if self.result.summary.use_polarisation:
            ax.text(45, -50, "Polarization:")

        ax.text(60, -20, f"alpha = {self.result.summary.alpha:.4f} ; "
                         f"R(m={self.result.config.M_ref:.1f}) = {self.result.summary.R_m_ref * 100:.1f}%")
        ax.text(60, -35, f"maximum dip = {self.result.summary.R_div_max * 100:.1f}% -> "
                         f"{E_LABEL[self.result.summary.ref_in_spec]}")
        if self.result.summary.use_polarisation:
            ax.text(60, -50, f"min = {self.result.summary.Pmin * 100:.1f}% ;"
                             f" avg = {self.result.summary.Pavg * 100:.1f}% -> "
                             f"{E_LABEL[self.result.summary.pol_in_spec]}")

        ax.set_xlim(0, 110)
        ax.set_ylim(-80, -2)

        evaluation = self.result.summary.evaluation.value
        if evaluation.startswith("Accepted"):
            eval_color = "#00aa00"
        elif evaluation.startswith("Rejected"):
            eval_color = "#aa0000"
        else:
            eval_color = "#aaaa00"

        if self.result.summary.ref_in_spec and self.result.summary.pol_in_spec:
            ax.text(
                74,
                0,
                evaluation + " - In Specification".upper(),
                fontweight="bold",
                color="#ffffff",
                backgroundcolor=eval_color,
            )
        else:
            ax.text(
                74,
                0,
                evaluation + " - Out of Specification".upper(),
                fontweight="bold",
                color="#ffffff",
                backgroundcolor=eval_color,
            )

        pol_str = " and polarization" if self.result.summary.use_polarisation else ""
        ax.text(62, -80, f"Data analysis of reflectivity:{pol_str}",
                fontsize=10, ha="center", fontweight="bold",
                )

    def plot_reflectivity(self):
        ax = self.fig.add_subplot(self.gs[4:9, 1:])
        ax.set_facecolor((0, 0, 0, 0))
        ax.set_title("Measured Reflectivity", fontsize=10)
        y_lim = [1e-2, 2.0]
        for data in self.result.data:
            y_lim[:] = min(y_lim[0], data.y.min()/2), max(y_lim[1], data.y.max()*2)
            plt.errorbar(
                data.x,
                data.y,
                xerr=data.dx,
                yerr=data.dy,
                label=data.label,
                color=data.color
            )
        plt.yscale("log"),

        plt.xlabel("Q [1/A]")
        plt.ylabel("R")

        plt.xlim(self.result.data[0].x.min() - 0.0025,
                 self.result.data[0].x.max() + 0.0025)
        plt.ylim(*y_lim)

        axl = plt.gca()
        axr = plt.twinx()
        lines, labels = axl.get_legend_handles_labels()
        lines2, labels2 = axr.get_legend_handles_labels()
        plt.legend(lines + lines2, labels + labels2, loc="lower left")
        plt.ylim(0, 1.5)

        axr.twiny()
        plt.xlabel("m-value")
        plt.ylabel("Intensity Modification")
        plt.xlim((self.result.data[0].x.min() - 0.0025) * Q2M,
                 (self.result.data[0].x.max() + 0.0025) * Q2M)

    def plot_corrected_reflectivity(self):
        if self.result.summary.use_polarisation:
            ax = self.fig.add_subplot(self.gs[11:16, 1:5])
        else:
            ax = self.fig.add_subplot(self.gs[11:16, 1:])

        ax.set_title("Corrected Reflectivity")
        ax.set_facecolor((0, 0, 0, 0))
        Q = self.result.data[0].x
        index_up = self.result.polar_pos.get(Polarization.po) \
            if self.result.polar_pos.get(Polarization.po) is not None \
            else self.result.polar_pos.get(Polarization.unpolarized)

        Rup = self.result.data[index_up].y

        ref = ideal_reflectivity(Q * Q2M, 1.0, self.result.config.alpha_spec, self.result.config.M_max)
        calc = ideal_reflectivity(Q * Q2M, self.result.summary.scale, self.result.summary.alpha,
                                  self.result.config.M_max)

        if (Rup < ref).any():
            plt.fill_between(
                Q,
                Rup,
                ref,
                where=(Rup < ref),
                color="#ff0000",
                alpha=0.3,
            )

        for data in self.result.data:
            plt.errorbar(
                data.x,
                data.y,
                xerr=data.dx,
                yerr=data.dy,
                label=data.label,
                color=data.color
            )

        plt.plot([-0.002, Q.max()-0.0135], [self.result.summary.R_m_ref, self.result.summary.R_m_ref], color="#aaaaaa",
                 linestyle="--")
        plt.plot(Q, calc, color="#aaaaaa", label="R(m,alpha)")
        plt.plot(Q, ref * self.result.config.R_ref, color="#ffdddd", linestyle="--",
                 label=f"{self.result.config.R_ref}*specification")
        plt.plot(Q, ref, color="#aa0000", label="specification")
        plt.plot([self.result.config.M_ref / Q2M], [self.result.config.R_ref], "o", color="#aa0000")

        plt.text(
            Q.max()-0.012,
            self.result.summary.R_m_ref,
            f"{self.result.summary.R_m_ref * 100:.1f} %",
            color="#aaaaaa",
            verticalalignment="center",
        )
        plt.text(1.0 / Q2M, 1.1, f"$\\alpha$-experimental = {self.result.summary.alpha:.3f}", color="#aaaaaa")
        plt.text(0.5 / Q2M, 0.61, f"$\\alpha$-specification = {self.result.config.alpha_spec:.3f}", color="#aa0000")

        plt.legend(loc="lower left", fontsize=10)
        plt.xlabel("Q [1/ A]")
        plt.ylabel("R")
        plt.xlim(Q.min(), Q.max())

        ax.twiny()
        plt.xlabel("m-value")
        plt.xlim(Q.min() * Q2M, Q.max() * Q2M)
        plt.ylim(0.0, 1.25)

    def plot_polarization(self):
        ax = self.fig.add_subplot(self.gs[11:16, 6:])
        ax.set_facecolor((0, 0, 0, 0))
        ax.set_title("Calculated Polarization")

        P = 100 * self.result.polarisation.y
        dP = 100 * self.result.polarisation.dy
        Q = self.result.polarisation.x

        ref = np.where(
            (Q >= self.result.config.Q_Pstart) & (Q <= self.result.config.Q_Pend),
            100 * self.result.config.P_min,
            np.nan
        )
        plt.errorbar(Q, P, yerr=dP, color=self.result.polarisation.color,
                     label=self.result.polarisation.label)

        if (P < ref).any():
            plt.fill_between(Q, P, ref, where=(P < ref), color="#ff0000", alpha=0.3)

        plt.plot(Q, ref, color="#aa0000", label="specification")
        plt.xlabel("Q [1/A]")
        plt.ylabel("Polarization [%]")
        plt.legend()
        plt.xlim(Q.min(), Q.max())
        plt.ylim(0, 105)

        ax.twiny()
        plt.xlabel("m-value")
        plt.xlim(Q.min() * Q2M, Q.max() * Q2M)

    def draw_parameters(self):
        ax = self.fig.add_subplot(self.gs[17:, :])
        ax.set_facecolor((0, 0, 0, 0))
        ax.axis("off")
        ax.text(50, 10, f"Correction completed in file: {self.result.main.filename}",
                horizontalalignment="center", fontdict={"fontweight": "bold"},
                fontsize=12)

        def wrap_list_of_strings(strings, max_width=52):
            wrapped = []
            for s in strings:
                lines = textwrap.wrap(s, width=max_width)
                wrapped.extend(lines)
            return wrapped

        correction = wrap_list_of_strings(self.result.main.correction)
        ax.text(
            0, 5, "\n".join(correction[:7]),
            va='top',
            fontsize=10.5

        )
        ax.text(
            60, 5, "\n".join(correction[7:15]),
            va='top',
            fontsize=10.5

        )
        ax.set_xlim(0, 110)
        ax.set_ylim(-80, -2)
