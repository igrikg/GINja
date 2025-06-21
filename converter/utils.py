import ast
import itertools
import numpy as np
from typing import Any, List, Union, Tuple
from dataclasses import fields, is_dataclass

from .datatypes import PolarizationEnum, SampleData
from .config import POLARISATION_STATES, POLARISATION_DEVICES


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
    samples_dict = samples_dict[0] if isinstance(samples_dict, Union[List, Tuple]) else samples_dict
    samples = [val for val in samples_dict.values() if sample_name == val.get('name')]
    if samples:
        field_names = [field.name for field in fields(SampleData)]
        filtered_dict = {k: v for k, v in samples[0].items() if k in field_names}
        return SampleData(**filtered_dict)
    return SampleData(sample_name)


def get_indexes(data: np.array, filter_value: Any) -> np.array:
    """

    :param data: array with data for search the
    :param filter_value: value which will be used for search
    :return: int(0,1) with 1 where merge with filter_value

    """
    return np.prod(data == filter_value, axis=1) if len(data.shape) > 1 \
        else np.array(data == filter_value).astype('int')


def filter_along_axis(arr: np.array, mask: np.array, axis: int) -> np.array:
    index = [slice(None)] * arr.ndim
    index[axis] = mask.astype('bool')
    return arr[tuple(index)]


def polarisation_filter(flippers_data: np.array, ydata: np.array,
                        polarisation: PolarizationEnum, axis=0) -> (np.array, np.array):
    """

    :param flippers_data: array of flippers data
    :param ydata: array for detector
    :param polarisation: Polarisarion stage
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
                field_map[f.name] = f.type(value)
            except Exception:
                field_map[f.name] = value
    return target_cls(**field_map)