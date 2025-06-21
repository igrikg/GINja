import argparse

from generator import ConfigReport, ReportGenerator, Q2M, AnalyserOrso

# Manual setup for argparse
parser = argparse.ArgumentParser(description="Generate reflectivity report")

# Positional arguments
parser.add_argument("input_file", type=str, help="Input data file")
parser.add_argument("mode", choices=["show", "make"], help="Display or generate PDF report")


# Optional arguments (mirroring ConfigReportInput)
parser.add_argument("--output_file", default=None, type=str, help="Output PDF filename")
parser.add_argument("--M_ref", type=float, default=2.0, help="location for reference reflectivity at high m")
parser.add_argument("--R_ref", type=float, default=0.9, help="reflectivity at reference location")
parser.add_argument("--R_div_max", type=float, default=0.1, help="maximum deviation from theoretical curve")

parser.add_argument("--M_max", type=float, default=2.2, help="m-value from specification (theoretical curve drop)")

parser.add_argument("--alpha_spec", type=float, default=0.075, help="alpha for theoretical curve")
parser.add_argument("--alpha_max", type=float, default=0.075, help="limit for measured alpha from specification")
parser.add_argument("--fit_alfa", type=str, choices=["true", "false"], default="true", help="evaluate alpha by fitting")

parser.add_argument("--P_min", type=float, default=0.95, help="minimum polarization over Q-range")

parser.add_argument("--Q_Pstart", type=float, default=0.022, help="start of Q-range evaluation")
parser.add_argument("--Q_Pend", type=float, default=6.2 / Q2M, help="end of Q-range evaluation")


# Parse CLI args
args = parser.parse_args()

# Build config from args
config = ConfigReport(
    M_ref=args.M_ref,
    R_ref=args.R_ref,
    R_div_max=args.R_div_max,
    M_max=args.M_max,
    alpha_spec=args.alpha_spec,
    alpha_max=args.alpha_max,
    fit_alfa=(args.fit_alfa.lower() == "true"),
    P_min=args.P_min,
    Q_Pstart=args.Q_Pstart,
    Q_Pend=args.Q_Pend,
)

report_data = AnalyserOrso(args.input_file, config).result
report = ReportGenerator(report_data)
if args.mode=="make":
    report.savepdf(args.output_file)
else:
    report.show()
