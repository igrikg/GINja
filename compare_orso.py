import sys
import os
import numpy as np
import matplotlib.pyplot as plt

try:
    from orsopy.fileio import load_orso
    HAS_ORSOPY = True
except ImportError:
    HAS_ORSOPY = False
    print("orsopy not found. Falling back to basic numpy parsing.")

def main():
    # If no files are provided, open a file dialog
    if len(sys.argv) < 2:
        print("Usage: python compare_orso.py <file1.ort> <file2.ort> ...")
        print("Opening file dialog to select files...")
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw() # Hide the main window
            files = filedialog.askopenfilenames(
                title="Select ORSO files to compare",
                filetypes=[("ORSO / Text files", "*.ort *.txt *.dat"), ("All files", "*.*")]
            )
            if not files:
                print("No files selected. Exiting.")
                return
        except Exception as e:
            print(f"Could not open file dialog: {e}")
            return
    else:
        files = sys.argv[1:]

    fig, ax = plt.subplots(figsize=(10, 6))
    
    for file_path in files:
        file_name = os.path.basename(file_path)
        success = False
        
        # 1. Try to load using orsopy (if available)
        if HAS_ORSOPY:
            try:
                datasets = load_orso(file_path)
                for i, dataset in enumerate(datasets):
                    # Identify columns
                    x_col_idx = 0
                    y_col_idx = 2 if len(dataset.info.columns) > 2 else 1
                    yerr_col_idx = 3 if len(dataset.info.columns) > 3 else None
                    
                    x_name = dataset.info.columns[0].name if hasattr(dataset.info.columns[0], 'name') else "X"
                    
                    # Look for R column
                    for idx, col in enumerate(dataset.info.columns):
                        if hasattr(col, 'name') and col.name == 'R':
                            y_col_idx = idx
                            break
                            
                    for idx, col in enumerate(dataset.info.columns):
                        if hasattr(col, 'error_of') and col.error_of == 'R':
                            yerr_col_idx = idx
                            break

                    x_data = dataset.data[:, x_col_idx]
                    y_data = dataset.data[:, y_col_idx]
                    y_err = dataset.data[:, yerr_col_idx] if yerr_col_idx is not None else None
                    
                    label = file_name
                    if len(datasets) > 1:
                        label += f" (Dataset {i+1})"
                    
                    if y_err is not None:
                        ax.errorbar(x_data, y_data, yerr=y_err, fmt='.-', label=label, capsize=3, alpha=0.8)
                    else:
                        ax.plot(x_data, y_data, '.-', label=label, alpha=0.8)
                        
                    if ax.get_xlabel() == "":
                        ax.set_xlabel(x_name)
                    if ax.get_ylabel() == "":
                        ax.set_ylabel("R")
                        
                success = True
            except Exception as e:
                print(f"orsopy failed to load {file_name}: {e}. Falling back to numpy.")
                
        # 2. Fallback to numpy.loadtxt (ORSO data lines are uncommented)
        if not success:
            try:
                data = np.loadtxt(file_path)
                if data.ndim == 1:
                    data = data.reshape(1, -1)
                
                x_data = data[:, 0]
                y_data = data[:, 2] if data.shape[1] > 2 else data[:, 1]
                y_err = data[:, 3] if data.shape[1] > 3 else None
                
                if y_err is not None:
                    ax.errorbar(x_data, y_data, yerr=y_err, fmt='.-', label=file_name, capsize=3, alpha=0.8)
                else:
                    ax.plot(x_data, y_data, '.-', label=file_name, alpha=0.8)
                    
                if ax.get_xlabel() == "":
                    ax.set_xlabel("X (First Column)")
                if ax.get_ylabel() == "":
                    ax.set_ylabel("Y (Third Column)")
            except Exception as e:
                print(f"Failed to load {file_name} with numpy: {e}")

    ax.set_yscale('log')
    ax.legend()
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.set_title("ORSO Data Comparison")
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
