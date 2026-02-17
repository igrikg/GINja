import os
import sys
import subprocess
import venv
import shutil
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop

def get_install_paths():
    """
    Returns a dictionary of paths based on whether the script is run as root or user.
    """
    if os.geteuid() == 0:
        # System-wide install (sudo)
        base_dir = "/usr/local/share/GINja"
        bin_link_dir = "/usr/local/bin"
        apps_dir = "/usr/share/applications"
        icons_dir = "/usr/share/pixmaps"
    else:
        # User install
        base_dir = os.path.expanduser("~/.local/share/GINja")
        bin_link_dir = os.path.expanduser("~/.local/bin")
        apps_dir = os.path.expanduser("~/.local/share/applications")
        icons_dir = os.path.expanduser("~/.local/share/icons")
    
    return {
        "base_dir": base_dir,
        "venv_dir": os.path.join(base_dir, "venv"),
        "bin_link_dir": bin_link_dir,
        "apps_dir": apps_dir,
        "icons_dir": icons_dir
    }

def create_desktop_file(name, display_name, command_path, icon_path, apps_dir):
    content = f"""[Desktop Entry]
Type=Application
Name={display_name}
Exec={command_path}
Icon={icon_path}
Terminal=false
Categories=Science;Education;
"""
    
    if not os.path.exists(apps_dir):
        os.makedirs(apps_dir)
        
    file_path = os.path.join(apps_dir, f"{name}.desktop")
    with open(file_path, "w") as f:
        f.write(content)
    print(f"Created desktop file: {file_path}")

def setup_private_venv_and_shortcuts():
    """
    Creates a private virtual environment, installs the package into it,
    creates desktop shortcuts, and symlinks binaries to bin dir.
    """
    try:
        paths = get_install_paths()
        venv_dir = paths["venv_dir"]
        
        print(f"Setting up private environment in {venv_dir}...")
        
        # 1. Create venv if not exists
        if not os.path.exists(venv_dir):
            os.makedirs(paths["base_dir"], exist_ok=True)
            subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        
        venv_python = os.path.join(venv_dir, "bin", "python")
        
        # Ensure pip is available
        try:
            subprocess.check_call([venv_python, "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print("pip not found in venv, trying ensurepip...")
            try:
                subprocess.check_call([venv_python, "-m", "ensurepip", "--upgrade", "--default-pip"])
            except subprocess.CalledProcessError:
                print("ensurepip failed. Please install python3-venv or python3-pip on your system.")
                raise

        # 2. Install this package into the venv
        source_dir = os.path.abspath(os.path.dirname(__file__))
        
        print(f"Installing dependencies and package into {venv_dir}...")
        subprocess.check_call([venv_python, "-m", "pip", "install", source_dir])
        
        # 3. Handle Icon
        icon_name = "BNC_logo.png"
        icon_src = os.path.join(source_dir, "themes", icon_name)
        icons_dir = paths["icons_dir"]
        
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
            
        icon_dest = os.path.join(icons_dir, "ginja_logo.png")
        
        if os.path.exists(icon_src):
            try:
                shutil.copy(icon_src, icon_dest)
            except Exception:
                pass
        else:
            icon_dest = ""

        # 4. Executables in the venv
        venv_bin_dir = os.path.join(venv_dir, "bin")
        converter_cmd = os.path.join(venv_bin_dir, "ginja-converter")
        report_cmd = os.path.join(venv_bin_dir, "ginja-report")
        
        # 5. Create desktop files
        create_desktop_file("ginja-converter", "GINja Converter", converter_cmd, icon_dest, paths["apps_dir"])
        create_desktop_file("ginja-report", "GINja Report", report_cmd, icon_dest, paths["apps_dir"])
        
        # 6. Symlink executables to bin_link_dir for CLI usage
        bin_link_dir = paths["bin_link_dir"]
        if not os.path.exists(bin_link_dir):
            os.makedirs(bin_link_dir)
            
        targets = ["ginja-converter", "ginja-report", "GINja_converter", "GINja_report", "GINja_nob_converter"]
        for target in targets:
            src = os.path.join(venv_bin_dir, target)
            dst = os.path.join(bin_link_dir, target)
            
            if os.path.exists(src):
                if os.path.exists(dst) or os.path.islink(dst):
                    try:
                        os.remove(dst)
                    except Exception:
                        pass
                try:
                    os.symlink(src, dst)
                    print(f"Linked {target} to {dst}")
                except Exception as e:
                    print(f"Failed to link {target}: {e}")
        
        print("Installation complete. Desktop shortcuts and CLI links created.")
        
    except Exception as e:
        print(f"Error setting up private environment: {e}")

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        try:
            install.run(self)
        except Exception as e:
            print(f"Standard install failed (expected on some systems): {e}")
            print("Proceeding with private environment setup...")

        setup_private_venv_and_shortcuts()

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        setup_private_venv_and_shortcuts()

setup(
    name="GINja",
    version="0.1.1",
    packages=find_packages(),
    py_modules=["converterGUI", "reportGUI", "ginja_converter_cli", "ginja_report_cli", "nob_type_converter"],
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "customtkinter",
        "nexusformat",
        "Pillow",
        "reportlab",
        "h5py",
        "orsopy",
        "scipy",
        "colored",
        "hdf5plugin",
        "PyYAML"
    ],
    entry_points={
        "console_scripts": [
            "ginja-converter=converterGUI:main",
            "ginja-report=reportGUI:main",
            "GINja_converter=ginja_converter_cli:main",
            "GINja_report=ginja_report_cli:main",
            "GINja_nob_converter=nob_type_converter:main",
        ],
    },
    package_data={
        "themes": ["*.json", "*.png"],
        "": ["*.json"],
    },
    include_package_data=True,
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
    },
    author="BNC",
    description="Reflectivity Data Reduction and Reporting Tool",
)
