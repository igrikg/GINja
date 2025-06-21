from orsopy.fileio import (Measurement as MeasurementBase, InstrumentSettings as InstrumentSettingsBase,
                           Person as PersonBase, Experiment as ExperimentBase)

from functools import wraps


def auto_fill_fields(**auto_fields):
    """
    Decorator to automatically fill specified fields on class instantiation
    if they are not provided.
    Usage:
      @auto_fill_fields(field1=default_value1, field2=default_value2)
      class MyDataClass:
          ...
    """

    def decorator(cls):
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            # For each auto field, fill it in kwargs if not already present
            for field_name, default_value in auto_fields.items():
                if field_name not in kwargs:
                    # Support callable default values (like default_factory)
                    value = default_value() if callable(default_value) else default_value
                    kwargs[field_name] = value
            original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator


Measurement = auto_fill_fields(scheme="angle-dispersive")(MeasurementBase)
InstrumentSettings = auto_fill_fields()(InstrumentSettingsBase)
Experiment = auto_fill_fields(probe='neutron', facility="BNC")(ExperimentBase)
Person = auto_fill_fields(affiliation="BNC user")(PersonBase)
