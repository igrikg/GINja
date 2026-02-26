import ast
import itertools
import numpy as np
from typing import Any, List, Union, Tuple
from collections import Counter
from dataclasses import fields, is_dataclass
from pprint import pprint
from .datatypes import PolarizationEnum, SampleData
from .config import POLARISATION_STATES, POLARISATION_DEVICES

def detect_patterns_multi(arr, max_len=4):
    """
    Detect repeating pattern for each column independently
    """
    n_rows, n_cols = arr.shape
    patterns = []

    for col in range(n_cols):
        col_data = arr[:, col]
        best_pattern = None
        best_score = -1

        for L in range(1, max_len + 1):
            if L > n_rows:
                break
            chunks = [col_data[i:i+L] for i in range(0, n_rows, L)]

            consensus = []
            for j in range(L):
                pos_vals = [chunk[j] for chunk in chunks if j < len(chunk)]
                if not pos_vals:
                    break
                most_common, count = Counter(pos_vals).most_common(1)[0]
                consensus.append(most_common)

            if len(consensus) != L:
                break

            score = sum(col_data[i] == consensus[i % L] for i in range(n_rows))

            if score > best_score:
                best_score = score
                best_pattern = consensus

        patterns.append(best_pattern)

    return patterns

def correct_array_multi(arr, patterns):
    n_rows, n_cols = arr.shape
    corrected = arr.copy()

    for col in range(n_cols):
        pattern = patterns[col]
        corrected[:, col] = [pattern[i % len(pattern)] for i in range(n_rows)]
    return corrected

def safety_div(first_arg, second_arg, epsilon=1e-12):
    second_safe = np.where(np.abs(second_arg) < epsilon, 1/epsilon, second_arg)
    return first_arg / second_safe


def get_polarisation(dev_list: List[str]) -> list[PolarizationEnum]:
    res = [('m', 'p') if dev in dev_list else ('o', 'o')
           for dev in POLARISATION_DEVICES]
    combinations = {PolarizationEnum(''.join(combo)) for combo in itertools.product(*res) if ''.join(combo) != 'oo'}
    return list(combinations) if combinations else [PolarizationEnum.unpolarized]


def get_sample_from_str(string: str, sample_name: str) -> SampleData:
    samples_dict = ast.literal_eval(string)
    if isinstance(samples_dict, (list, tuple)):
        if len(samples_dict) == 1:
            samples_dict = samples_dict[0]
            samples_list = [samples_dict] if isinstance(samples_dict, dict) else samples_dict
        else:
            samples_list = samples_dict
    else:
        samples_list = [samples_dict] if isinstance(samples_dict, dict) else samples_dict
    samples = [val for val in samples_list if isinstance(val, dict) and sample_name == val.get('name')]
    if samples:
        field_names = [field.name for field in fields(SampleData)]
        filtered_dict = {k: v for k, v in samples[0].items() if k in field_names}
        return SampleData(**filtered_dict)
    return SampleData(sample_name)


def get_indexes(data: np.typing.NDArray, filter_value: Any) -> np.typing.NDArray:
    """

    :param data: array with data for search the
    :param filter_value: value which will be used for search
    :return: int(0,1) with 1 where merge with filter_value

    """
    return np.prod(data == filter_value, axis=1) if len(data.shape) > 1 \
        else np.array(data == filter_value).astype('int')


def filter_along_axis(arr: np.typing.NDArray, mask: np.typing.NDArray, axis: int) -> np.typing.NDArray:
    # Create a tuple of slices for dimensions before and after the axis
    pre_slices = (slice(None),) * axis
    post_slices = (slice(None),) * (arr.ndim - axis - 1)
    # Apply the mask at the specified axis
    return arr[pre_slices + (mask.astype(bool),) + post_slices]

def fix_flipper_position(flippers_data: np.typing.NDArray)->np.typing.NDArray:
    patterns = detect_patterns_multi(flippers_data, max_len=4)
    res= correct_array_multi(flippers_data, patterns)
    return res



def polarisation_filter(flippers_data: np.typing.NDArray, ydata: np.typing.NDArray,
                        polarisation: PolarizationEnum, axis=0) -> np.typing.NDArray:
    """

    :param flippers_data: array of flippers data
    :param ydata: array for detector
    :param polarisation: Polarisation stage
    :param axis: it is needed to filter for other axis in ydata
    :return: filtered ydata
    """
    if polarisation is PolarizationEnum.unpolarized:
        return ydata
    filter_value = [POLARISATION_STATES.get(symbol) for symbol in polarisation.value if symbol != 'o']
    filter_data = get_indexes(flippers_data, filter_value)

    return filter_along_axis(ydata, filter_data, axis)

def convert_dataclass(src, target_cls):
    assert is_dataclass(src) and is_dataclass(target_cls), "Both must be dataclasses"

    field_map = {}
    for f in fields(target_cls):
        value = getattr(src, f.name, None)
        if value is not None:
            try:
                if hasattr(f.type, '__origin__') and f.type.__origin__ is Union: # Handle Union types
                    # For simplicity, if it's a Union, we try to convert to the first type that isn't None
                    # A more robust solution might involve checking if value is instance of one of the types
                    non_none_types = [t for t in f.type.__args__ if t is not type(None)]
                    if non_none_types: # If there are actual types in the Union
                        field_map[f.name] = non_none_types[0](value)
                    else:
                        field_map[f.name] = value # Fallback if only None in Union or other issues
                elif isinstance(f.type, type) and not is_dataclass(f.type):
                    field_map[f.name] = f.type(value)
                elif is_dataclass(f.type):
                    field_map[f.name] = convert_dataclass(value, f.type)  # Recursive call for nested dataclasses
                else:
                    field_map[f.name] = value # Direct assignment for other types
            except Exception:
                field_map[f.name] = value
    return target_cls(**field_map)


def regions_overlap(region1: Tuple[int, int, int, int], region2: Tuple[int, int, int, int]) -> bool:
    y1_min, y1_max, x1_min, x1_max = region1
    y2_min, y2_max, x2_min, x2_max = region2
    return not (y2_max < y1_min or y2_min > y1_max or x2_max < x1_min or x2_min > x1_max)
