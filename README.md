# GINja — Reflectometry Data Conversion and Reporting Tools

**GINja** is a Python-based CLI toolkit for converting raw reflectometry data from the **[GINA reflectometer](https://bnc.hu/gina/)** into standardized [ORSO](https://www.reflectometry.org/) format files, visualizing results, and preparing NOB ORSO type file.

---

## ✨ Features

- Convert GINA `.nxs` or `.dat` files to ORSO `.ort` format
- Apply detector, background, normalization, and reduction corrections
- Generate visual or PDF reflectivity reports
- Convert detector images to NOB-type ORSO files for PSI reporting

---

## 📦 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/igrikg/GINja.git
   cd GINja

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # On Windows: .venv\Scripts\activate
   
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt

---

##  🚀 Usage
###   🔁 converter.py — Convert raw scans to ORSO format
   ```bash
   python converter.py [-options] filename
   ```
   **Positional:**

   * `filename`: Input scan file (`.nxs` or `.dat`)

   **Key optional arguments:**
   * `-h`, `--help`: show help message and exit
   * `--outputName`: Output filename (default: `name_of_raw_file.ort`)
   * `--folder_of_input`: Folder where input file is located
   * `--folder_of_output_file`: Specific folder to save output file

   **Detector Settings:**
   * `--source_detector`
   * `--source_region`

   **Normalisation Settings:**
   * `--norm_time`: `{true,false}` 
   * `--norm_monitor`: `{true,false}`
   * `--norm_intensity_norm`: `{true,false}`
   * `--norm_intensity_norm_type`: `{constValue,maxValue,maxValueGlobal,psdRegion}`
   * `--norm_intensity_value`:
   * `--norm_intensity_point_number`:
   * `--norm_intensity_region`:

   **Reduction Settings:**
   * `--red_foot_print_correction`: `{true,false}`
   * `--red_absorption_correction`: `{true,false}`
   * `--red_polarisation_correction`: `{true,false}`
   * `--red_mu_type`: `{constValue,typical}`
   * `--red_mu_enum`: `{glass,Si,SiO2}`
   * `--red_mu_value`:
   
   **Background Settings:**
   * `--bg_use_correction`: `{true,false}`
   * `--bg_correction_type`: `{constValue,psdRegion,extraFile}`
   * `--bg_file`:
   * `--bg_value`:
   * `--bg_region`:

**Example:**
   ```bash
    python converter.py data.nxs \
      --norm_time true \
      --red_foot_print_correction false \
      --bg_use_correction true \
      --outputName sample.ort
   ```

### 🧾report.py — Generate reflectivity report (PDF or figure)
   ```bash
   python report.py input_file {show,make} [options]
   ```
 
   **Positional:**
   * `input_file`: Path to `.ort` file
   * `show`: Display interactive figure
   * `make`: Save report as PDF
   
   **Key options:**
   * `--output_file`: Output PDF filename
   * ` --M_ref`: location for reference reflectivity at high m
   * `--R_ref`:  reflectivity at reference location
   * `--R_div_max`: maximum deviation from theoretical curve
   * `--M_max`: m-value from specification (theoretical curve drop)
   * `--alpha_spec`: alpha for theoretical curve
   * `--alpha_max`: limit for measured alpha from specification
   * `--fit_alfa`:  evaluate alpha by fitting like `{true,false}`
   * `--P_min`: minimum polarization over Q-range
   * `--Q_Pstart`: start of Q-range evaluation
   * `--Q_Pend`: end of Q-range evaluation
   * `-h`, `--help`: show help message and exit

      **Example:**
      ```bash
      python report.py sample.ort make --output_file report.pdf --fit_alfa true
      ```
### 📸 nob_type_converter.py — Convert detector image to NOB-type ORSO file
   ```bash
   python nob_type_converter.py filename detector [--region y1 y2 x1 x2]
   ```
   **Positional:**
   * `filename`: Input `.dat` or `.nxs` file 
   * `detector`: Name of detector or ROI 

   **Optional:**
   * `--region`: Specify ROI region: `y1 y2 x1 x2`
   * `-h`, `--help`: show help message and exit

   **Example:**
   ```bash
   python nob_type_converter.py detector.npy rear_detector --region 100 200 50 150
   ```

---

## 📁 Project Structure
   ``` bash
   GINja/
   ├── converter/                # Main converter to ORSO package
   ├── generator/                # Reflectivity figure/PDF generator package
   ├── convert_to_narziss/       # NOB-type file converter package 
   ├── requirements.txt
   ├── converter.py              # Main converter to ORSO
   ├── report.py                 # Reflectivity figure/PDF generator
   ├── nob_type_converter.py     # Converts 2D detector data to NOB-type file
   ├── README.md
   └── .venv/                    # Local virtual environment (not committed)
   ```

---

## 🧪 Sample Workflow
```bash
   # Step 1: Convert to ORSO
   python converter.py raw_data.nxs --outputName sample.ort

   # Step 2: Show report
   python report.py sample.ort show

   # Step 3: Create PDF report
   python report.py sample.ort make --output_file report.pdf
```

---
 
## 📋 Requirements
    
* Python 3.10+
* `numpy`
* `pandas`
* `nexusformat`
* `orsopy`
* `scipy`
* `matplotlib`

**Install all dependencies with:**
```bash
    pip install -r requirements.txt
```

---

## 📄 License
This project is licensed under the [MIT License](https://rem.mit-license.org/).

Feel free to use, modify, and share with attribution.

---


## 🙏 Acknowledgements
Responsible for GINA Reflectometer @ BNC

Uses ORSO as standard output format

PSI NOB-type converter added for institutional reporting needs

Have feedback or want to contribute?
Open an issue or submit a pull request!

---

## 🙋 Feedback & Contributions

Have feedback or want to contribute?  
[Open an issue](https://github.com/igrikg/GINja/issues) or submit a pull request!