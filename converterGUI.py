import os
import sys
import ast
import json
from dataclasses import dataclass, fields, asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Union, get_origin, get_args, Iterable, List

try:
    import tkinter
    import tkinter.filedialog
    import tkinter.messagebox
    import customtkinter as ctk
    from PIL import Image
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
except ImportError as e:
    print(f"Error: Failed to import GUI dependencies: {e}", file=sys.stderr)
    print("Please ensure 'python3-tk' is installed on your system (e.g., 'sudo apt install python3-tk').", file=sys.stderr)
    print("Also ensure all pip requirements are installed.", file=sys.stderr)
    sys.exit(1)

from converter import (MadeConversion, get_data, CorrectionParameters, DataSourceConfig,
                       NormalisationConfig, ReductionConfig, BackgroundConfig)
from converter.check_config import check_config
from converter.datatypes import MuDataEnum, AdsorptionTypeCorrection, BackgroundTypeCorrection, IntensityTypeCorrection, DataSet, PolarizationEnum
from converter.metadata import Metadata


@dataclass
class ConverterConfig:
    source: DataSourceConfig
    norm: NormalisationConfig
    red: ReductionConfig
    bg: BackgroundConfig
    output_name: str = ""
    folder_of_input: bool = False
    folder_of_output: str = ""


def save_config(config: ConverterConfig, filename):
    data = asdict(config)
    
    class EnumEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Enum):
                return obj.name
            return super().default(obj)

    with open(filename, "w") as f:
        json.dump(data, f, indent=2, cls=EnumEncoder)


def load_config(filename) -> ConverterConfig:
    try:
        with open(filename) as f:
            data = json.load(f)
        
        def dict_to_dataclass(cls, d):
            if not is_dataclass(cls):
                return d
            field_types = {f.name: f.type for f in fields(cls)}
            kwargs = {}
            for f in fields(cls):
                if f.name in d:
                    val = d[f.name]
                    ft = field_types[f.name]
                    
                    if get_origin(ft) is Union:
                        args = get_args(ft)
                        non_none_args = [t for t in args if t is not type(None)]
                        if non_none_args:
                            ft = non_none_args[0]

                    if isinstance(ft, type) and issubclass(ft, Enum):
                        try:
                            val = ft[val]
                        except KeyError:
                            pass
                    
                    kwargs[f.name] = val
            return cls(**kwargs)

        source = dict_to_dataclass(DataSourceConfig, data.get('source', {}))
        norm = dict_to_dataclass(NormalisationConfig, data.get('norm', {}))
        red = dict_to_dataclass(ReductionConfig, data.get('red', {}))
        bg = dict_to_dataclass(BackgroundConfig, data.get('bg', {}))
        
        return ConverterConfig(
            source=source,
            norm=norm,
            red=red,
            bg=bg,
            output_name=data.get('output_name', ""),
            folder_of_input=data.get('folder_of_input', False),
            folder_of_output=data.get('folder_of_output', "")
        )

    except (FileNotFoundError, json.JSONDecodeError):
        return ConverterConfig(
            source=DataSourceConfig(),
            norm=NormalisationConfig(),
            red=ReductionConfig(),
            bg=BackgroundConfig()
        )


class ConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ORSO Converter GUI")
        self.geometry("1600x900")
        ctk.set_appearance_mode("light")

        # Resolve resource paths
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        theme_path = os.path.join(self.base_path, "themes", "violet.json")
        
        if os.path.exists(theme_path):
            ctk.set_default_color_theme(theme_path)
        else:
            print(f"Warning: Theme file not found at {theme_path}, using default.")
            ctk.set_default_color_theme("blue") # Fallback

        self.config_data = load_config('converter_config.json')
        self.input_file = ''
        self.data_object: Union[Metadata, None] = None
        self.filename_var = ctk.StringVar(value="No file selected")
        self.auto_update_var = ctk.BooleanVar(value=True) # Always true
        self.status_var = ctk.StringVar(value="Ready")
        
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Sidebar Container (Fixed)
        # Increased width to 500
        self.sidebar = ctk.CTkFrame(self, width=500)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.main_area = ctk.CTkFrame(self)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.inputs = {} # Key -> (Variable, TypeHint)
        self.widgets = {} # Key -> Widget
        self.rows = {} # Key -> Row Frame
        self.region_vars = {} 
        self.region_labels = {}

        self.build_sidebar()
        self.build_main_area()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.update_config_from_ui()
        save_config(self.config_data, 'converter_config.json')
        self.destroy()

    def build_sidebar(self):
        self.top_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.top_frame.pack(fill="x", side="top", padx=5, pady=5)
        # Logo
        try:
            logo_path = os.path.join(self.base_path, "themes", "BNC_logo.png")
            if os.path.exists(logo_path):
                logo_image = ctk.CTkImage(
                    light_image=Image.open(logo_path),
                    dark_image=Image.open(logo_path),
                    size=(150, 56)
                )
                logo_label = ctk.CTkLabel(self.top_frame, image=logo_image, text="")
                logo_label.pack(pady=(0, 10))
        except Exception as e:
            print(f"Error loading logo: {e}")

        self.scrollable_frame = ctk.CTkScrollableFrame(self.sidebar, width=450)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # File Selection
        ctk.CTkLabel(self.scrollable_frame, text="Input File", font=("Arial", 14, "bold")).pack(pady=(5, 5), anchor="w")
        file_frame = ctk.CTkFrame(self.scrollable_frame)
        file_frame.pack(fill="x", pady=5)
        
        entry = ctk.CTkEntry(file_frame, textvariable=self.filename_var, state="disabled")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        
        open_button = ctk.CTkButton(file_frame, text="Open", width=60, command=self.load_file)
        open_button.pack(side="right", padx=5)

        # Output Options
        ctk.CTkLabel(self.scrollable_frame, text="Output Options", font=("Arial", 14, "bold")).pack(pady=(5, 5), anchor="w")
        
        self.inputs['output_name'] = (ctk.StringVar(value=self.config_data.output_name), str)
        
        # Folder of input checkbox with trace
        var_folder_input = ctk.BooleanVar(value=self.config_data.folder_of_input)
        self.inputs['folder_of_input'] = (var_folder_input, bool)
        var_folder_input.trace_add("write", self.toggle_output_folder_state)

        self.file_out_frame = ctk.CTkFrame(self.scrollable_frame)
        self.file_out_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(self.file_out_frame, text="Output Filename (Optional)").pack(side="left",  padx=5)
        ctk.CTkCheckBox(self.file_out_frame, text="Save in Input Folder", variable=self.inputs['folder_of_input'][0], command=self.toggle_output_folder_state).pack(
            side="right",fill="x", padx=5, pady=5)
        ctk.CTkEntry(self.file_out_frame, textvariable=self.inputs['output_name'][0]).pack(side="bottom", fill="x", padx=5, pady=2)

        self.inputs['folder_of_output'] = (ctk.StringVar(value=self.config_data.folder_of_output), str)
        
        self.output_folder_label = ctk.CTkLabel(self.scrollable_frame, text="Output Folder")
        self.output_folder_label.pack(anchor="w", padx=5)
        
        self.output_folder_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.output_folder_frame.pack(fill="x", padx=5, pady=2)
        
        out_entry = ctk.CTkEntry(self.output_folder_frame, textvariable=self.inputs['folder_of_output'][0])
        out_entry.pack(side="left", fill="x", expand=True)
        self.widgets['output_folder_entry'] = out_entry
        
        out_btn = ctk.CTkButton(self.output_folder_frame, text="...", width=30, command=self.select_output_folder)
        out_btn.pack(side="right", padx=(5,0))
        self.widgets['output_folder_button'] = out_btn

        # Config Sections
        self.create_config_section("Data Source", self.config_data.source, DataSourceConfig, "source")
        self.create_config_section("Normalisation", self.config_data.norm, NormalisationConfig, "norm")
        self.create_config_section("Reduction", self.config_data.red, ReductionConfig, "red")
        self.create_config_section("Background", self.config_data.bg, BackgroundConfig, "bg")

        # 2. Footer Area (Fixed at bottom of sidebar)
        self.footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.footer_frame.pack(fill="x", side="bottom", padx=5, pady=5)

        # Convert Button
        ctk.CTkButton(self.footer_frame, text="CONVERT & SAVE", command=self.run_conversion_and_save, height=40, fg_color="green", hover_color="darkgreen").pack(pady=(1, 1), fill="x")

        # Status Label
        ctk.CTkLabel(self.footer_frame, textvariable=self.status_var, text_color="gray").pack(side="bottom", pady=1)
        
        # Initial state update
        self.toggle_output_folder_state()
        self.on_parameter_change()

    def toggle_output_folder_state(self, *args):
        if not hasattr(self, 'output_folder_frame') or not hasattr(self, 'output_folder_label'):
            return
            
        try:
            is_checked = self.inputs['folder_of_input'][0].get()
            if is_checked:
                self.inputs['folder_of_output'][0].set("")
                self.output_folder_label.pack_forget()
                self.output_folder_frame.pack_forget()
            else:
                self.output_folder_label.pack(anchor="w", padx=5, after=self.file_out_frame)
                self.output_folder_frame.pack(fill="x", padx=5, pady=2, after=self.output_folder_label)
        except Exception as e:
            print(f"Error toggling state: {e}")

    def on_parameter_change(self, *args):
        self.check_source_visibility()
        self.check_normalisation_visibility()
        self.check_reduction_visibility()
        self.check_background_visibility()
        if self.auto_update_var.get() and self.data_object:
            self.update_preview()

    def check_source_visibility(self):
        if 'source_detector' not in self.inputs or 'source_region_frame' not in self.widgets:
            return
        
        detector = self.inputs['source_detector'][0].get()
        if detector == "2Ddata":
            self.widgets['source_region_frame'].pack(fill="x", pady=5)
            self.update_region_limits()
        else:
            self.widgets['source_region_frame'].pack_forget()

    def check_normalisation_visibility(self):
        if 'norm_intensity_norm' not in self.inputs:
            return

        is_norm_enabled = self.inputs['norm_intensity_norm'][0].get()
        norm_type = self.inputs['norm_intensity_norm_type'][0].get() if 'norm_intensity_norm_type' in self.inputs else None

        # Iterate over fields in order to maintain layout order
        for field in fields(NormalisationConfig):
            key = f"norm_{field.name}"
            
            # Special handling for intensity_region
            if field.name == 'intensity_region':
                if 'norm_intensity_region_frame' in self.widgets:
                    if is_norm_enabled and norm_type == "psdRegion":
                        self.widgets['norm_intensity_region_frame'].pack(fill="x", pady=2)
                    else:
                        self.widgets['norm_intensity_region_frame'].pack_forget()
                continue

            if key not in self.rows:
                continue
            
            # Always show main switch
            if field.name == 'intensity_norm':
                self.rows[key].pack(fill="x", pady=2)
                continue
            
            # Always show time/monitor
            if field.name in ['time', 'monitor']:
                self.rows[key].pack(fill="x", pady=2)
                continue

            # Dependent fields
            if field.name in ['intensity_norm_type', 'intensity_value', 'intensity_point_number']:
                if not is_norm_enabled:
                    self.rows[key].pack_forget()
                    continue
                
                # Enabled, check specific conditions
                if field.name == 'intensity_norm_type':
                    self.rows[key].pack(fill="x", pady=2)
                
                elif field.name == 'intensity_value':
                    if norm_type == "constValue":
                        self.rows[key].pack(fill="x", pady=2)
                    else:
                        self.rows[key].pack_forget()
                
                elif field.name == 'intensity_point_number':
                    if norm_type == "psdRegion":
                        self.rows[key].pack(fill="x", pady=2)
                    else:
                        self.rows[key].pack_forget()

    def check_reduction_visibility(self):
        # Hide polarisation correction always for now
        if 'red_polarisation_correction' in self.rows:
            self.rows['red_polarisation_correction'].pack_forget()

        if 'red_absorption_correction' not in self.inputs:
            return

        is_abs_enabled = self.inputs['red_absorption_correction'][0].get()
        mu_type = self.inputs['red_mu_type'][0].get() if 'red_mu_type' in self.inputs else None
        
        # Mu fields
        mu_fields = ['red_mu_type', 'red_mu_enum', 'red_mu_value']
        
        if not is_abs_enabled:
            for field in mu_fields:
                if field in self.rows:
                    self.rows[field].pack_forget()
        else:
            # Absorption enabled
            if 'red_mu_type' in self.rows:
                self.rows['red_mu_type'].pack(fill="x", pady=2)
            
            if 'red_mu_enum' in self.rows:
                if mu_type == "typical":
                    self.rows['red_mu_enum'].pack(fill="x", pady=2)
                else:
                    self.rows['red_mu_enum'].pack_forget()
            
            if 'red_mu_value' in self.rows:
                if mu_type == "constValue":
                    self.rows['red_mu_value'].pack(fill="x", pady=2)
                else:
                    self.rows['red_mu_value'].pack_forget()

    def check_background_visibility(self):
        if 'bg_use_correction' not in self.inputs:
            return

        is_bg_enabled = self.inputs['bg_use_correction'][0].get()
        bg_type = self.inputs['bg_correction_type'][0].get() if 'bg_correction_type' in self.inputs else None

        # Iterate over fields in order to maintain layout order
        for field in fields(BackgroundConfig):
            key = f"bg_{field.name}"

            # Special handling for bg_region
            if field.name == 'region':
                if 'bg_region_frame' in self.widgets:
                    if is_bg_enabled and bg_type == "psdRegion":
                        self.widgets['bg_region_frame'].pack(fill="x", pady=2)
                    else:
                        self.widgets['bg_region_frame'].pack_forget()
                continue
            
            # Special handling for bg_file
            if field.name == 'file':
                if 'bg_file_frame' in self.widgets:
                    if is_bg_enabled and bg_type == "extraFile":
                        self.widgets['bg_file_frame'].pack(fill="x", pady=2)
                    else:
                        self.widgets['bg_file_frame'].pack_forget()
                continue

            if key not in self.rows:
                continue
            
            # Always show main switch
            if field.name == 'use_correction':
                self.rows[key].pack(fill="x", pady=2)
                continue

            # Dependent fields
            if field.name in ['correction_type', 'value']:
                if not is_bg_enabled:
                    self.rows[key].pack_forget()
                    continue
                
                if field.name == 'correction_type':
                    self.rows[key].pack(fill="x", pady=2)
                
                elif field.name == 'value':
                    if bg_type == "constValue":
                        self.rows[key].pack(fill="x", pady=2)
                    else:
                        self.rows[key].pack_forget()

    def update_region_limits(self):
        if not self.data_object:
            return
        try:
            pols = self.data_object.polarisation
            pol = pols[0] if pols else PolarizationEnum.unpolarized
            
            if '2Ddata' in self.data_object.detectors_list:
                data = self.data_object.get_dataset('2Ddata', pol)
                if data.ndim >= 3:
                    ymax, xmax = data.shape[1], data.shape[2]
                    if 'x_label' in self.region_labels:
                        self.region_labels['x'].configure(text=f"X Range (Max: {xmax})")
                    if 'y_label' in self.region_labels:
                        self.region_labels['y'].configure(text=f"Y Range (Max: {ymax})")
        except Exception as e:
            print(f"Error getting 2D limits: {e}")

    def create_config_section(self, title, config_obj, config_cls, prefix):
        ctk.CTkLabel(self.scrollable_frame, text=title, font=("Arial", 14, "bold")).pack(pady=(20, 5), anchor="w")
        
        section_frame = ctk.CTkFrame(self.scrollable_frame)
        section_frame.pack(fill="x", pady=5)

        for field in fields(config_cls):
            val = getattr(config_obj, field.name)
            field_type = field.type
            
            if get_origin(field_type) is Union:
                args = get_args(field_type)
                non_none_args = [t for t in args if t is not type(None)]
                if non_none_args:
                    field_type = non_none_args[0]

            key = f"{prefix}_{field.name}"

            # Special handling for region field in DataSourceConfig
            if key == "source_region":
                self.region_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
                self.widgets['source_region_frame'] = self.region_frame
                
                ymin, ymax, xmin, xmax = 0, 0, 0, 0
                if val and len(val) >= 4:
                    ymin, ymax, xmin, xmax = val[0], val[1], val[2], val[3]
                
                self.region_vars['xmin'] = ctk.IntVar(value=xmin)
                self.region_vars['xmax'] = ctk.IntVar(value=xmax)
                self.region_vars['ymin'] = ctk.IntVar(value=ymin)
                self.region_vars['ymax'] = ctk.IntVar(value=ymax)

                x_row = ctk.CTkFrame(self.region_frame, fg_color="transparent")
                x_row.pack(fill="x", pady=2)
                self.region_labels['x'] = ctk.CTkLabel(x_row, text="X Range", width=80, anchor="w")
                self.region_labels['x'].pack(side="left", padx=5)
                ctk.CTkEntry(x_row, textvariable=self.region_vars['xmin'], width=60).pack(side="left", padx=2)
                ctk.CTkLabel(x_row, text="-").pack(side="left")
                ctk.CTkEntry(x_row, textvariable=self.region_vars['xmax'], width=60).pack(side="left", padx=2)

                y_row = ctk.CTkFrame(self.region_frame, fg_color="transparent")
                y_row.pack(fill="x", pady=2)
                self.region_labels['y'] = ctk.CTkLabel(y_row, text="Y Range", width=80, anchor="w")
                self.region_labels['y'].pack(side="left", padx=5)
                ctk.CTkEntry(y_row, textvariable=self.region_vars['ymin'], width=60).pack(side="left", padx=2)
                ctk.CTkLabel(y_row, text="-").pack(side="left")
                ctk.CTkEntry(y_row, textvariable=self.region_vars['ymax'], width=60).pack(side="left", padx=2)
                
                # Bind events
                for child in x_row.winfo_children():
                    if isinstance(child, ctk.CTkEntry):
                        child.bind("<FocusOut>", self.on_parameter_change)
                        child.bind("<Return>", self.on_parameter_change)
                for child in y_row.winfo_children():
                    if isinstance(child, ctk.CTkEntry):
                        child.bind("<FocusOut>", self.on_parameter_change)
                        child.bind("<Return>", self.on_parameter_change)

                continue

            # Special handling for intensity_region in NormalisationConfig
            if key == "norm_intensity_region":
                self.norm_region_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
                self.widgets['norm_intensity_region_frame'] = self.norm_region_frame
                
                ymin, ymax, xmin, xmax = 0, 0, 0, 0
                if val and len(val) >= 4:
                    ymin, ymax, xmin, xmax = val[0], val[1], val[2], val[3]
                
                self.region_vars['norm_xmin'] = ctk.IntVar(value=xmin)
                self.region_vars['norm_xmax'] = ctk.IntVar(value=xmax)
                self.region_vars['norm_ymin'] = ctk.IntVar(value=ymin)
                self.region_vars['norm_ymax'] = ctk.IntVar(value=ymax)

                x_row = ctk.CTkFrame(self.norm_region_frame, fg_color="transparent")
                x_row.pack(fill="x", pady=2)
                ctk.CTkLabel(x_row, text="X Range", width=80, anchor="w").pack(side="left", padx=5)
                ctk.CTkEntry(x_row, textvariable=self.region_vars['norm_xmin'], width=60).pack(side="left", padx=2)
                ctk.CTkLabel(x_row, text="-").pack(side="left")
                ctk.CTkEntry(x_row, textvariable=self.region_vars['norm_xmax'], width=60).pack(side="left", padx=2)

                y_row = ctk.CTkFrame(self.norm_region_frame, fg_color="transparent")
                y_row.pack(fill="x", pady=2)
                ctk.CTkLabel(y_row, text="Y Range", width=80, anchor="w").pack(side="left", padx=5)
                ctk.CTkEntry(y_row, textvariable=self.region_vars['norm_ymin'], width=60).pack(side="left", padx=2)
                ctk.CTkLabel(y_row, text="-").pack(side="left")
                ctk.CTkEntry(y_row, textvariable=self.region_vars['norm_ymax'], width=60).pack(side="left", padx=2)
                
                # Bind events
                for child in x_row.winfo_children():
                    if isinstance(child, ctk.CTkEntry):
                        child.bind("<FocusOut>", self.on_parameter_change)
                        child.bind("<Return>", self.on_parameter_change)
                for child in y_row.winfo_children():
                    if isinstance(child, ctk.CTkEntry):
                        child.bind("<FocusOut>", self.on_parameter_change)
                        child.bind("<Return>", self.on_parameter_change)

                continue

            # Special handling for bg_file and bg_region
            if key == "bg_file":
                self.bg_file_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
                self.widgets['bg_file_frame'] = self.bg_file_frame

                var = ctk.StringVar(value=str(val) if val is not None else "")
                self.inputs[key] = (var, str)

                file_row = ctk.CTkFrame(self.bg_file_frame, fg_color="transparent")
                file_row.pack(fill="x", pady=2)
                ctk.CTkLabel(file_row, text="File", width=150, anchor="w").pack(side="left", padx=5)
                
                file_entry = ctk.CTkEntry(file_row, textvariable=var)
                file_entry.pack(side="left", fill="x", expand=True)
                file_entry.bind("<FocusOut>", self.on_parameter_change)
                file_entry.bind("<Return>", self.on_parameter_change)
                self.widgets['bg_file_entry'] = file_entry

                file_btn = ctk.CTkButton(file_row, text="...", width=30, command=self.select_background_file)
                file_btn.pack(side="right", padx=(5,0))
                self.widgets['bg_file_button'] = file_btn
                continue

            if key == "bg_region":
                self.bg_region_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
                self.widgets['bg_region_frame'] = self.bg_region_frame
                
                ymin, ymax, xmin, xmax = 0, 0, 0, 0
                if val and len(val) >= 4:
                    ymin, ymax, xmin, xmax = val[0], val[1], val[2], val[3]
                
                self.region_vars['bg_xmin'] = ctk.IntVar(value=xmin)
                self.region_vars['bg_xmax'] = ctk.IntVar(value=xmax)
                self.region_vars['bg_ymin'] = ctk.IntVar(value=ymin)
                self.region_vars['bg_ymax'] = ctk.IntVar(value=ymax)

                x_row = ctk.CTkFrame(self.bg_region_frame, fg_color="transparent")
                x_row.pack(fill="x", pady=2)
                ctk.CTkLabel(x_row, text="X Range", width=80, anchor="w").pack(side="left", padx=5)
                ctk.CTkEntry(x_row, textvariable=self.region_vars['bg_xmin'], width=60).pack(side="left", padx=2)
                ctk.CTkLabel(x_row, text="-").pack(side="left")
                ctk.CTkEntry(x_row, textvariable=self.region_vars['bg_xmax'], width=60).pack(side="left", padx=2)

                y_row = ctk.CTkFrame(self.bg_region_frame, fg_color="transparent")
                y_row.pack(fill="x", pady=2)
                ctk.CTkLabel(y_row, text="Y Range", width=80, anchor="w").pack(side="left", padx=5)
                ctk.CTkEntry(y_row, textvariable=self.region_vars['bg_ymin'], width=60).pack(side="left", padx=2)
                ctk.CTkLabel(y_row, text="-").pack(side="left")
                ctk.CTkEntry(y_row, textvariable=self.region_vars['bg_ymax'], width=60).pack(side="left", padx=2)
                
                # Bind events
                for child in x_row.winfo_children():
                    if isinstance(child, ctk.CTkEntry):
                        child.bind("<FocusOut>", self.on_parameter_change)
                        child.bind("<Return>", self.on_parameter_change)
                for child in y_row.winfo_children():
                    if isinstance(child, ctk.CTkEntry):
                        child.bind("<FocusOut>", self.on_parameter_change)
                        child.bind("<Return>", self.on_parameter_change)
                continue


            row = ctk.CTkFrame(section_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            self.rows[key] = row # Store row for visibility toggling
            
            label = ctk.CTkLabel(row, text=field.name.replace("_", " ").title(), width=150, anchor="w")
            label.pack(side="left", padx=5)

            # Special handling for detector field
            if key == "source_detector":
                var = ctk.StringVar(value=str(val))
                widget = ctk.CTkOptionMenu(row, variable=var, values=[str(val)], command=self.on_parameter_change)
                widget.pack(side="left", fill="x", expand=True)
                self.inputs[key] = (var, str)
                self.widgets[key] = widget
                continue

            if field_type == bool:
                var = ctk.BooleanVar(value=val)
                widget = ctk.CTkCheckBox(row, text="", variable=var, command=self.on_parameter_change)
                widget.pack(side="left")
                self.inputs[key] = (var, bool)
                self.widgets[key] = widget
            
            elif isinstance(field_type, type) and issubclass(field_type, Enum):
                var = ctk.StringVar(value=val.name if isinstance(val, Enum) else str(val))
                options = [e.name for e in field_type]
                widget = ctk.CTkOptionMenu(row, variable=var, values=options, command=self.on_parameter_change)
                widget.pack(side="left", fill="x", expand=True)
                self.inputs[key] = (var, field_type)
                self.widgets[key] = widget
            
            elif field_type in (int, float):
                var = ctk.StringVar(value=str(val))
                widget = ctk.CTkEntry(row, textvariable=var)
                widget.pack(side="left", fill="x", expand=True)
                widget.bind("<FocusOut>", self.on_parameter_change)
                widget.bind("<Return>", self.on_parameter_change)
                self.inputs[key] = (var, field_type)
                self.widgets[key] = widget
            
            elif field_type == str:
                var = ctk.StringVar(value=str(val) if val is not None else "")
                widget = ctk.CTkEntry(row, textvariable=var)
                widget.pack(side="left", fill="x", expand=True)
                widget.bind("<FocusOut>", self.on_parameter_change)
                widget.bind("<Return>", self.on_parameter_change)
                self.inputs[key] = (var, str)
                self.widgets[key] = widget

            elif get_origin(field_type) is Iterable or field_type == list or field_type == tuple:
                str_val = str(val) if val is not None else ""
                var = ctk.StringVar(value=str_val)
                widget = ctk.CTkEntry(row, textvariable=var, placeholder_text="e.g. [1, 2]")
                widget.pack(side="left", fill="x", expand=True)
                widget.bind("<FocusOut>", self.on_parameter_change)
                widget.bind("<Return>", self.on_parameter_change)
                self.inputs[key] = (var, "iterable")
                self.widgets[key] = widget
            
            else:
                var = ctk.StringVar(value=str(val))
                widget = ctk.CTkEntry(row, textvariable=var)
                widget.pack(side="left", fill="x", expand=True)
                widget.bind("<FocusOut>", self.on_parameter_change)
                widget.bind("<Return>", self.on_parameter_change)
                self.inputs[key] = (var, str)
                self.widgets[key] = widget

    def load_file(self):
        path = tkinter.filedialog.askopenfilename(filetypes=[("NXS/DAT Files", "*.nxs *.dat"), ("All Files", "*.*")])
        if path:
            self.filename_var.set(Path(path).name)
            self.input_file = path
            #try:
            if 1:
                self.data_object = get_data(self.input_file)
                
                # Update detector list
                if self.data_object:
                    detectors = self.data_object.detectors_list
                    if 'source_detector' in self.widgets:
                        widget = self.widgets['source_detector']
                        if isinstance(widget, ctk.CTkOptionMenu):
                            widget.configure(values=detectors)
                            current = self.inputs['source_detector'][0].get()
                            if current not in detectors and detectors:
                                self.inputs['source_detector'][0].set(detectors[0])

                self.status_var.set("File loaded")
                self.on_parameter_change()
            #except Exception as e:
            #    print(f"Error loading file: {e}")
            #    self.status_var.set("Error loading file")
            #    tkinter.messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def select_background_file(self):
        file_path = tkinter.filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            self.inputs['bg_file'][0].set(file_path)
            self.on_parameter_change()

    def select_output_folder(self):
        path = tkinter.filedialog.askdirectory()
        if path:
            self.inputs['folder_of_output'][0].set(path)

    def try_auto_update(self, *args):
        # Deprecated, use on_parameter_change
        self.on_parameter_change()

    def build_main_area(self):
        # Main area only contains plot now
        self.build_plot()

    def build_plot(self):
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Reflectivity")
        self.ax.set_xlabel("Q ($Å^{-1}$)")
        self.ax.set_ylabel("R")
        self.ax.grid(True)
        
        # Frame for canvas and toolbar
        plot_container = ctk.CTkFrame(self.main_area, fg_color="white")
        plot_container.pack(fill="both", expand=True)

        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, plot_container)
        toolbar.update()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_config_from_ui(self):
        self.config_data.output_name = self.inputs['output_name'][0].get()
        self.config_data.folder_of_input = self.inputs['folder_of_input'][0].get()
        self.config_data.folder_of_output = self.inputs['folder_of_output'][0].get()

        def update_obj(obj, prefix):
            for field in fields(obj):
                key = f"{prefix}_{field.name}"
                
                # Special handling for source_region
                if key == "source_region":
                    if 'xmin' in self.region_vars:
                        try:
                            xmin = self.region_vars['xmin'].get()
                            xmax = self.region_vars['xmax'].get()
                            ymin = self.region_vars['ymin'].get()
                            ymax = self.region_vars['ymax'].get()
                            # reduction.py expects [ymin, ymax, xmin, xmax]
                            setattr(obj, field.name, [ymin, ymax, xmin, xmax])
                        except:
                            setattr(obj, field.name, None)
                    continue

                # Special handling for norm_intensity_region
                if key == "norm_intensity_region":
                    if 'norm_xmin' in self.region_vars:
                        try:
                            xmin = self.region_vars['norm_xmin'].get()
                            xmax = self.region_vars['norm_xmax'].get()
                            ymin = self.region_vars['norm_ymin'].get()
                            ymax = self.region_vars['norm_ymax'].get()
                            setattr(obj, field.name, [ymin, ymax, xmin, xmax])
                        except:
                            setattr(obj, field.name, None)
                    continue

                # Special handling for bg_region
                if key == "bg_region":
                    if 'bg_xmin' in self.region_vars:
                        try:
                            xmin = self.region_vars['bg_xmin'].get()
                            xmax = self.region_vars['bg_xmax'].get()
                            ymin = self.region_vars['bg_ymin'].get()
                            ymax = self.region_vars['bg_ymax'].get()
                            setattr(obj, field.name, [ymin, ymax, xmin, xmax])
                        except:
                            setattr(obj, field.name, None)
                    continue

                if key in self.inputs:
                    input_data = self.inputs[key]
                    
                    if isinstance(input_data, tuple):
                        var, type_hint = input_data
                        val_str = var.get()
                        
                        if type_hint == bool:
                            setattr(obj, field.name, var.get())

                        elif type_hint == "iterable":
                            if val_str.strip():
                                try:
                                    final_val = ast.literal_eval(val_str)
                                    setattr(obj, field.name, final_val)
                                except Exception:
                                    try:
                                        items = [float(x.strip()) for x in val_str.split(",")]
                                        setattr(obj, field.name, items)
                                    except:
                                        setattr(obj, field.name, None)
                            else:
                                setattr(obj, field.name, None)
                        
                        elif isinstance(type_hint, type) and issubclass(type_hint, Enum):
                            setattr(obj, field.name, type_hint[val_str])
                        
                        elif type_hint == int:
                            try:
                                setattr(obj, field.name, int(val_str))
                            except ValueError:
                                pass
                        
                        elif type_hint == float:
                            try:
                                setattr(obj, field.name, float(val_str))
                            except ValueError:
                                pass
                        
                        else:
                            setattr(obj, field.name, val_str)

        update_obj(self.config_data.source, "source")
        update_obj(self.config_data.norm, "norm")
        update_obj(self.config_data.red, "red")
        update_obj(self.config_data.bg, "bg")

    def update_plot(self, datasets: List[DataSet]):
        self.figure.clf()
        ax = self.figure.add_subplot(111)
        
        for ds in datasets:
            q = ds.result.Q
            r = ds.result.R
            dr = ds.result.dR
            
            label = "Data"
            try:
                if ds.measurement.instrument_settings.polarization:
                    label = ds.measurement.instrument_settings.polarization.name
            except:
                pass
            
            if q is not None and r is not None:
                ax.errorbar(q, r, yerr=dr, fmt='.-', label=label, capsize=2)
        
        ax.set_xlabel("Q ($Å^{-1}$)")
        ax.set_ylabel("R")
        ax.set_yscale('log')
        ax.set_title("Reflectivity")
        ax.legend()
        ax.grid(True, which="both", ls="-", alpha=0.5)
        
        self.canvas.draw()

    def get_parameters(self):
        self.update_config_from_ui()
        cmd = "GUI_Conversion"
        return CorrectionParameters(
            data_source=self.config_data.source,
            normalisation=self.config_data.norm,
            reduction=self.config_data.red,
            background=self.config_data.bg,
            program_call=cmd
        )

    def update_preview(self):
        if not self.data_object:
            return

        #try:
        if 1:
            parameters = self.get_parameters()
            converter = MadeConversion(self.data_object, parameters)
            results = converter.result
            self.update_plot(results)
            self.status_var.set("Plot updated")
        #except Exception as e:
        #    print(f"Preview error: {e}")
        #    self.status_var.set(f"Preview error: {e}")

    def run_conversion_and_save(self):
        if not self.input_file:
            tkinter.messagebox.showwarning("Warning", "No input file selected!")
            return
        
        if not self.data_object:
            try:
                self.data_object = get_data(self.input_file)
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Failed to load file:\n{e}")
                return

        try:
            parameters = self.get_parameters()
            print(f"Processing {self.input_file}...")
            check_config(parameters, self.data_object)
            
            output_name = self.config_data.output_name if self.config_data.output_name else None
            folder_output = self.config_data.folder_of_output if self.config_data.folder_of_output else None
            
            converter = MadeConversion(self.data_object, parameters)
            
            # Update plot
            results = converter.result
            self.update_plot(results)
            
            # Save file
            converter.create_orso(
                filename=output_name,
                path=folder_output,
                folder_input_file=self.config_data.folder_of_input
            )
            print("Conversion successful!")
            self.status_var.set("Conversion saved")
            tkinter.messagebox.showinfo("Success", "Conversion completed and saved!")
            
        except Exception as e:
            print(f"Error during conversion: {e}")
            self.status_var.set("Conversion failed")
            tkinter.messagebox.showerror("Error", f"Conversion failed:\n{e}")


def main():
    app = ConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
