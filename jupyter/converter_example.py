# %% [markdown]
# # GINja Data Converter Example
# This notebook demonstrates how to process data files, override metadata, perform data reduction, and export to ORSO format programmatically, doing exactly what the GINja Converter GUI does behind the scenes!

# %%
import os
import sys
import copy
import numpy as np
import matplotlib.pyplot as plt

# Add the parent directory to the path so we can import GINja modules
sys.path.append(os.path.abspath('..'))

from converter.iofile import get_data
from converter.datatypes import (DataSourceConfig, NormalisationConfig, ReductionConfig, 
                                BackgroundConfig, CorrectionParameters, AdsorptionTypeCorrection,
                                IntensityTypeCorrection)
from converter.reduction import DataReduction as MadeConversion
from converter.orso_convert import OrsoData

# %% [markdown]
# ## 1. Load Data
# Select a file and load it using `get_data`.

# %%
file_path = '../GINA_260413_00000740.dat'  # Change this to your actual .dat file path
if not os.path.exists(file_path):
    print(f"File not found: {file_path}. Please update the file_path variable above.")
else:
    data_object = get_data(file_path)
    print(f"Loaded {os.path.basename(file_path)}")
    print("Detectors available:", data_object.detectors_list)

# %% [markdown]
# ## 2. Override Metadata (Optional)
# Just like in the GUI, you can override Sample dimensions or Slit parameters if they are incorrect in the file.

# %%
if 'data_object' in locals():
    # Override Sample length
    new_sample = copy.copy(data_object.sample)
    new_sample.length = 10.0  # mm
    data_object.sample_override = new_sample
    
    # Override Slit configuration
    new_slit = copy.copy(data_object.slit_configuration)
    new_slit.slit1_width = 1.0  # mm
    new_slit.slit2_width = 1.0  # mm
    data_object.slit_override = new_slit
    print("Metadata overridden successfully.")

# %% [markdown]
# ## 3. Configure Correction Parameters
# Set up the data source, normalisation, reduction, and background configurations.

# %%
if 'data_object' in locals():
    parameters = CorrectionParameters(
        data_source=DataSourceConfig(
            detector='2Ddata', 
            # Define your custom ROI here: [ymin, ymax, xmin, xmax]
            # Set to None if you don't want to use a Custom ROI
            region=[30, 80, 400, 600] 
        ),
        normalisation=NormalisationConfig(
            time=True, 
            monitor=True, 
            intensity_norm=True,
            intensity_norm_type=IntensityTypeCorrection.constValue,
            intensity_value=1.0
        ),
        reduction=ReductionConfig(
            foot_print_correction=True, 
            absorption_correction=True,
            mu_type=AdsorptionTypeCorrection.constValue,
            mu_value=0.0
        ),
        background=BackgroundConfig(
            use_correction=True, 
            value=1e-12
        )
    )
    print("Configuration created.")

# %% [markdown]
# ## 4. Perform Data Reduction
# Run the conversion process to calculate Theta, Q, R, and dR.

# %%
if 'data_object' in locals():
    converter = MadeConversion(data_object, parameters)
    dataset_list = converter.get_datasets()
    result = dataset_list[0]
    
    print("Reduction complete!")
    print(f"Extracted {len(result.theta)} points.")
    print("Theta array shape:", result.theta.shape)
    print("Reflectivity (R) array shape:", result.result.R.shape)

# %% [markdown]
# ## 5. Plot 1D Reflectivity
# Visualize the reduced Reflectivity data using Matplotlib.

# %%
if 'data_object' in locals():
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Plot R vs Theta
    ax.errorbar(result.theta, result.result.R, yerr=result.result.dR, 
                fmt='.-', label='Reflectivity', capsize=3)
    
    ax.set_yscale('log')
    ax.set_xlabel('Theta (deg)')
    ax.set_ylabel('Reflectivity (R)')
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend()
    plt.title(f"1D Reflectivity: {os.path.basename(file_path)}")
    plt.tight_layout()
    plt.show()

# %% [markdown]
# ## 6. Export to ORSO format
# Save the results to `.ort` files. It will create a standard Q-based file and an extra Theta-based file, just like the GUI does!

# %%
if 'data_object' in locals():
    output_filename = "notebook_output"
    
    orso_saver = OrsoData(dataset_list, parameters)
    orso_saver.save(output_filename)
    
    print(f"Data saved to:")
    print(f"1. {output_filename}.ort (Q vs R)")
    print(f"2. {output_filename}_theta.ort (Theta vs R)")
