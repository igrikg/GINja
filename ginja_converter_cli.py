"""
Program to create ORSO file
"""

import argparse
import ast
from enum import Enum
import sys
import shlex

from converter import (MadeConversion, get_data, CorrectionParameters, DataSourceConfig,
                       NormalisationConfig, ReductionConfig, BackgroundConfig)

from dataclasses import fields, MISSING
from typing import Type, Union

from converter.check_config import check_config


def add_dataclass_to_group(parser: argparse.ArgumentParser, config_class: Type, group_name: str, prefix: str = ""):
    group = parser.add_argument_group(group_name)
    for field in fields(config_class):
        arg_name = f"--{prefix}{field.name}"
        default = field.default if field.default is not MISSING else None
        arg_type = field.type

        # Handle Union and Optionals
        if hasattr(arg_type, '__origin__') and arg_type.__origin__ is Union:
            arg_type = next(t for t in arg_type.__args__ if t is not type(None))

        # Handle Enums
        if isinstance(default, Enum):
            group.add_argument(arg_name, type=str, choices=[e.name for e in arg_type], default=default.name)
        elif arg_type == bool:
            group.add_argument(arg_name, type=str, choices=["true", "false"], default=str(default).lower())
        elif arg_type in [int, float, str]:
            group.add_argument(arg_name, type=arg_type, default=default)
        else:
            group.add_argument(arg_name, type=ast.literal_eval, default=default)


# 🛠 Convert argparse.Namespace to dataclass instance
def parse_args_to_dataclass(args: argparse.Namespace, config_class: Type, prefix: str = ""):
    kwargs = {}
    for field in fields(config_class):
        arg_name = f"{prefix}{field.name}"
        val = getattr(args, arg_name)

        if field.type == bool or (hasattr(field.type, '__origin__') and bool in field.type.__args__):
            val = str(val).lower() == "true"

        if isinstance(field.default, Enum):
            enum_type = field.default.__class__
            val = enum_type[val]

        kwargs[field.name] = val
    return config_class(**kwargs)

def main():
    description="The program reads data from scan file in the .nxs or .dat(nicos scan) format , \
           performs various corrections, conversations and projections and exports\
           the resulting reflectivity in an orso format."

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("filename",
                        help="input file name (default name_of_raw_file.ort)")

    file_data = parser.add_argument_group('Files information')


    file_data.add_argument("-o", "--outputName",
                            default = None,
                            help = "output file name (default name_of_raw_file.ort in folder of cli run)")

    file_data.add_argument("-fif", "--folder_of_input",
                           default=False,
                           help="output file save in the folder with raw file")

    file_data.add_argument("-op", "--folder_of_output_file",
                           default=None,
                           help="use special folder for output file with name name_of_raw_file.ort")

    add_dataclass_to_group(parser, DataSourceConfig, "Detector Settings", prefix="source_")
    add_dataclass_to_group(parser, NormalisationConfig, "Normalisation Settings", prefix="norm_")
    add_dataclass_to_group(parser, ReductionConfig, "Reduction Settings", prefix="red_")
    add_dataclass_to_group(parser, BackgroundConfig, "Background Settings", prefix="bg_")

    args = parser.parse_args()

    source_cfg = parse_args_to_dataclass(args, DataSourceConfig, prefix="source_")
    norm_cfg = parse_args_to_dataclass(args, NormalisationConfig, prefix="norm_")
    red_cfg = parse_args_to_dataclass(args, ReductionConfig, prefix="red_")
    bg_cfg = parse_args_to_dataclass(args, BackgroundConfig, prefix="bg_")
    cmd = "python " + shlex.quote(sys.argv[0]) + " " + " ".join(shlex.quote(a) for a in sys.argv[1:])
    parameters = CorrectionParameters(data_source=source_cfg,
                                      normalisation=norm_cfg,
                                      reduction=red_cfg,
                                      background=bg_cfg,
                                      program_call=cmd)
    data = get_data(args.filename)
    check_config(parameters, data)
    res = MadeConversion(data, parameters).create_orso(filename=getattr(args, 'outputName'),
                                                       path=getattr(args, 'folder_of_output_file'),
                                                       folder_input_file=bool(getattr(args, 'folder_of_input')))


if __name__ == "__main__":
    main()
