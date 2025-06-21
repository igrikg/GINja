import argparse
from convert_to_narziss.converttonarziss import get_data, create_orso


def main():
    parser = argparse.ArgumentParser(description=
                                     "Process detector data to convert NOB type ORSO file for PSI report generator.")

    parser.add_argument("filename", help="Path to the input data file (.nxs, .dat)")
    parser.add_argument("detector", help="Name of detector or ROI. For nexus file 2Ddata "
                                         "coresponding to 2D picture. Use --region to set ROI in this case.")
    parser.add_argument("--region", type=int, nargs=4, metavar=('y1', 'y2', 'x1', 'x2'),
                        help="ROI region for 2Ddata detector: y1 y2 x1 y1")

    args = parser.parse_args()
    data = get_data(args.filename)
    create_orso(data, args.detector, args.region)


if __name__ == "__main__":
    main()