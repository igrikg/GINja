import numpy as np
import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from converter.iofile import NexusFile, ScanDataReader, ScanDataFile, relative_to_full_path, load_tiff_pil, get_data
from converter.datatypes import PolarizationEnum, PersonData, ExperimentData, SampleData, MeasurementData


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class TestRelativeToFullPath:
    def test_relative_to_full_path(self):
        result = relative_to_full_path("/path/to/file.dat", "other.dat")
        assert result == "/path/to/other.dat"

    def test_relative_to_full_path_with_subdir(self):
        result = relative_to_full_path("/path/to/file.dat", "subdir/other.dat")
        assert result == "/path/to/subdir/other.dat"


class TestLoadTiffPil:
    def test_load_tiff_pil(self):
        with tempfile.NamedTemporaryFile(suffix='.tiff', delete=False) as f:
            from PIL import Image
            img = Image.new('L', (10, 10))
            img.save(f.name)
            f.flush()
            
            result = load_tiff_pil(f.name)
            os.unlink(f.name)
            
            assert result.shape == (10, 10)


class TestNexusFile:
    @pytest.fixture
    def nexus_file(self):
        nxs_path = os.path.join(DATA_DIR, 'GINA_p260209_scan_00000349_theta_twotheta_flipper_1.nxs')
        if not os.path.exists(nxs_path):
            pytest.skip("Nexus file not found")
        return NexusFile(nxs_path, fix_polarisation=False)
    
    def test_nexus_file_init(self, nexus_file):
        assert nexus_file.file_path is not None
        assert nexus_file.nxfile is not None
    
    def test_src_path(self, nexus_file):
        assert nexus_file.src_path is not None
    
    def test_instrument_name(self, nexus_file):
        result = nexus_file.instrument_name
        assert result is not None
    
    def test_instrument(self, nexus_file):
        result = nexus_file.instrument
        assert result is not None
    
    def test_nxdata(self, nexus_file):
        result = nexus_file.nxdata
        assert result is not None
    
    def test_entry(self, nexus_file):
        result = nexus_file.entry
        assert result is not None
    
    def test_detectors_list(self, nexus_file):
        result = nexus_file.detectors_list
        assert isinstance(result, list)
        assert '2Ddata' in result
    
    def test_dev_list(self, nexus_file):
        result = nexus_file.dev_list
        assert isinstance(result, list)
        assert 'theta' in result
    
    def test_monitor(self, nexus_file):
        result = nexus_file.monitor
        assert isinstance(result, np.ndarray)
    
    def test_time(self, nexus_file):
        result = nexus_file.time
        assert isinstance(result, np.ndarray)
    
    def test_polarisation(self, nexus_file):
        result = nexus_file.polarisation
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_flippers_data_no_fix(self, nexus_file):
        result = nexus_file.flippers_data
        assert isinstance(result, np.ndarray)
    
    def test_get_dataset(self, nexus_file):
        result = nexus_file.get_dataset('2Ddata', PolarizationEnum.po)
        assert result is not None
    
    def test_get_dataset_monitor(self, nexus_file):
        result = nexus_file.get_dataset_monitor(PolarizationEnum.po)
        assert isinstance(result, np.ndarray)
    
    def test_get_dataset_time(self, nexus_file):
        result = nexus_file.get_dataset_time(PolarizationEnum.po)
        assert isinstance(result, np.ndarray)
    
    def test_owner(self, nexus_file):
        result = nexus_file.owner
        assert isinstance(result, PersonData)
    
    def test_experiment(self, nexus_file):
        result = nexus_file.experiment
        assert isinstance(result, ExperimentData)
    
    def test_sample(self, nexus_file):
        result = nexus_file.sample
        assert isinstance(result, SampleData)
    
    def test_measurement(self, nexus_file):
        result = nexus_file.measurement(PolarizationEnum.po)
        assert isinstance(result, MeasurementData)
    
    def test_slit_configuration(self, nexus_file):
        result = nexus_file.slit_configuration
        assert result is not None
    
    def test_instrument_settings(self, nexus_file):
        result = nexus_file.instrument_settings(PolarizationEnum.po)
        assert result is not None


class TestNexusFileWithFixPolarisation:
    @pytest.fixture
    def nexus_file(self):
        nxs_path = os.path.join(DATA_DIR, 'GINA_p260209_scan_00000349_theta_twotheta_flipper_1.nxs')
        if not os.path.exists(nxs_path):
            pytest.skip("Nexus file not found")
        return NexusFile(nxs_path, fix_polarisation=True)
    
    def test_flippers_data_with_fix(self, nexus_file):
        result = nexus_file.flippers_data
        assert isinstance(result, np.ndarray)


class TestNexusFileMultipleScans:
    @pytest.fixture
    def nexus_file_350(self):
        nxs_path = os.path.join(DATA_DIR, 'GINA_p260209_scan_00000350_theta_twotheta_flipper_1.nxs')
        if not os.path.exists(nxs_path):
            pytest.skip("Nexus file not found")
        return NexusFile(nxs_path)
    
    def test_polarisation_350(self, nexus_file_350):
        result = nexus_file_350.polarisation
        assert len(result) > 0
    
    def test_detectors_list_350(self, nexus_file_350):
        result = nexus_file_350.detectors_list
        assert isinstance(result, list)


class TestScanDataFile:
    @pytest.fixture
    def dat_file(self):
        dat_path = os.path.join(DATA_DIR, 'p260209_00000349.dat')
        if not os.path.exists(dat_path):
            pytest.skip("DAT file not found")
        return ScanDataFile(dat_path)
    
    def test_scan_data_file_init(self, dat_file):
        assert dat_file.file_path is not None
    
    def test_scan_data_file_metadata(self, dat_file):
        result = dat_file.metadata
        assert isinstance(result, dict)
    
    def test_scan_data_file_dataset(self, dat_file):
        result = dat_file.dataset
        assert result is not None
    
    def test_scan_data_file_detectors_list(self, dat_file):
        result = dat_file.detectors_list
        assert isinstance(result, list)
    
    def test_scan_data_file_dev_list(self, dat_file):
        result = dat_file.dev_list
        assert isinstance(result, list)
    
    def test_scan_data_file_monitor(self, dat_file):
        result = dat_file.monitor
        assert isinstance(result, np.ndarray)
    
    def test_scan_data_file_time(self, dat_file):
        result = dat_file.time
        assert isinstance(result, np.ndarray)
    
    def test_scan_data_file_polarisation(self, dat_file):
        result = dat_file.polarisation
        assert isinstance(result, list)
    
    def test_scan_data_file_flippers_data(self, dat_file):
        result = dat_file.flippers_data
        assert isinstance(result, np.ndarray)
    
    def test_scan_data_file_get_dataset(self, dat_file):
        detectors = dat_file.detectors_list
        if detectors:
            result = dat_file.get_dataset(detectors[0], PolarizationEnum.unpolarized)
            assert result is not None
    
    def test_scan_data_file_owner(self, dat_file):
        result = dat_file.owner
        assert isinstance(result, PersonData)
    
    def test_scan_data_file_experiment(self, dat_file):
        result = dat_file.experiment
        assert isinstance(result, ExperimentData)
    
    def test_scan_data_file_sample(self, dat_file):
        result = dat_file.sample
        assert isinstance(result, SampleData)
    
    def test_scan_data_file_slit_configuration(self, dat_file):
        result = dat_file.slit_configuration
        assert result is not None
    
    def test_scan_data_file_instrument_settings(self, dat_file):
        result = dat_file.instrument_settings(PolarizationEnum.unpolarized)
        assert result is not None
    
    def test_scan_data_file_measurement(self, dat_file):
        result = dat_file.measurement(PolarizationEnum.unpolarized)
        assert result is not None


class TestScanDataReader:
    @pytest.fixture
    def dat_file(self):
        dat_path = os.path.join(DATA_DIR, 'p260209_00000349.dat')
        if not os.path.exists(dat_path):
            pytest.skip("DAT file not found")
        return ScanDataReader(dat_path)
    
    def test_parse_file(self, dat_file):
        assert dat_file.header is not None
        assert len(dat_file.header) > 0
    
    def test_header_units(self, dat_file):
        assert dat_file.header_units is not None
    
    def test_dataframe(self, dat_file):
        assert dat_file.df is not None
        assert len(dat_file.df) > 0
    
    def test_get_devices(self, dat_file):
        result = dat_file.get_devices()
        assert isinstance(result, list)
    
    def test_get_detectors(self, dat_file):
        result = dat_file.get_detectors()
        assert isinstance(result, list)


class TestNexusFileWithoutFlipper:
    @pytest.fixture
    def nexus_file_no_flipper(self):
        nxs_path = os.path.join(DATA_DIR, 'GINA_p260209_scan_00000399_theta_twotheta.nxs')
        if not os.path.exists(nxs_path):
            pytest.skip("Nexus file not found")
        return NexusFile(nxs_path, fix_polarisation=False)
    
    def test_flippers_data_empty(self, nexus_file_no_flipper):
        result = nexus_file_no_flipper.flippers_data
        assert len(result) == 0
    
    def test_get_dataset_no_flipper(self, nexus_file_no_flipper):
        result = nexus_file_no_flipper.get_dataset('2Ddata', PolarizationEnum.unpolarized)
        assert result is not None
    
    def test_flippers_data_with_flipper_no_fix(self):
        nxs_path = os.path.join(DATA_DIR, 'GINA_p260209_scan_00000349_theta_twotheta_flipper_1.nxs')
        if not os.path.exists(nxs_path):
            pytest.skip("Nexus file not found")
        nf = NexusFile(nxs_path, fix_polarisation=False)
        result = nf.flippers_data
        assert isinstance(result, np.ndarray)
    
    def test_flippers_data_with_fix(self):
        nxs_path = os.path.join(DATA_DIR, 'GINA_p260209_scan_00000349_theta_twotheta_flipper_1.nxs')
        if not os.path.exists(nxs_path):
            pytest.skip("Nexus file not found")
        nf = NexusFile(nxs_path, fix_polarisation=True)
        result = nf.flippers_data
        assert isinstance(result, np.ndarray)


class TestScanDataReaderEdgeCases:
    def test_parse_file_with_empty_lines(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00

# filepath : /path/to/file.dat
# number : 1


### Experiment information


# Exp_proposal : PROJ1234


### Scan data
# theta	;	detector
0.1	;	1.0
### End of test
""")
            f.flush()
            
            reader = ScanDataReader(f.name)
            os.unlink(f.name)
            
            assert reader.header is not None
    
    def test_parse_file_without_colon_in_metadata(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# title
# Scan data
# theta ; detector
0.1	;	1.0
""")
            f.flush()
            
            reader = ScanDataReader(f.name)
            os.unlink(f.name)
            
            assert reader.header is not None
    
    def test_load_2d_data_nonexistent_files(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# filepath : /path/to/file.dat
# number : 1
### Scan data
# theta	;	detector	file0.tiff
0.1	;	1.0	file0.tiff
""")
            f.flush()
            
            reader = ScanDataReader(f.name)
            os.unlink(f.name)
            
            assert reader.header is not None
    
    def test_get_tiff_column_no_tiff(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# title: Test
# Scan data
# theta	;	detector
0.1	;	1.0
""")
            f.flush()
            
            reader = ScanDataReader(f.name)
            os.unlink(f.name)
            
            result = reader._ScanDataReader__get_tiff_column_name()
            assert result is None


class TestScanDataFileEdgeCases:
    def test_owner_string_no_braces(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# filepath : /path/to/file.dat
# number : 1
### Experiment information
# Exp_proposal : PROJ1234
# Exp_title : Test
# Exp_users : user1, user2
### Sample and alignment
# Sample_samplename : test_sample
### Instrument setup
# wavelength_value : 5.0 A
# slit_1_value : 0.1 mm
# d_slit_1_value : 100.0 mm
# slit_2_value : 0.2 mm
# d_slit_2_value : 200.0 mm
### Scan data
# theta	;	detector	ante_monitor	ante_timer
0.1	;	1.0	100	10.0
### End of test
""")
            f.flush()
            
            scan_file = ScanDataFile(f.name)
            os.unlink(f.name)
            
            result = scan_file.owner
            assert result.name == "user1"
    
    def test_owner_dict_single_user(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# filepath : /path/to/file.dat
# number : 1
### Experiment information
# Exp_proposal : PROJ1234
# Exp_title : Test
# Exp_users : {'name': 'Test User', 'email': 'test@test.com'}
### Sample and alignment
# Sample_samplename : test_sample
### Instrument setup
# wavelength_value : 5.0 A
# slit_1_value : 0.1 mm
# d_slit_1_value : 100.0 mm
# slit_2_value : 0.2 mm
# d_slit_2_value : 200.0 mm
### Scan data
# theta	;	detector	ante_monitor	ante_timer
0.1	;	1.0	100	10.0
### End of test
""")
            f.flush()
            
            scan_file = ScanDataFile(f.name)
            os.unlink(f.name)
            
            result = scan_file.owner
            assert result.name == "Test User"
    
    def test_flippers_data_empty(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# filepath : /path/to/file.dat
# number : 1
### Experiment information
# Exp_proposal : PROJ1234
# Exp_title : Test
# Exp_users : test_user
### Sample and alignment
# Sample_samplename : test_sample
### Instrument setup
# wavelength_value : 5.0 A
### Scan data
# theta	;	detector	ante_monitor	ante_timer
0.1	;	1.0	100	10.0
### End of test
""")
            f.flush()
            
            scan_file = ScanDataFile(f.name)
            os.unlink(f.name)
            
            result = scan_file.flippers_data
            assert len(result) == 0
    
    def test_flippers_data_with_flipper_no_fix(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# filepath : /path/to/file.dat
# number : 1
### Experiment information
# Exp_proposal : PROJ1234
# Exp_title : Test
# Exp_users : test_user
### Sample and alignment
# Sample_samplename : test_sample
### Instrument setup
# wavelength_value : 5.0 A
### Scan data
# theta	flipper_1	;	detector	ante_monitor	ante_timer
0.1	on	;	1.0	100	10.0
### End of test
""")
            f.flush()
            
            scan_file = ScanDataFile(f.name, fix_polarisation=False)
            os.unlink(f.name)
            
            result = scan_file.flippers_data
            assert isinstance(result, np.ndarray)
    
    def test_get_dataset_empty_flippers(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# filepath : /path/to/file.dat
# number : 1
### Experiment information
# Exp_proposal : PROJ1234
# Exp_title : Test
# Exp_users : test_user
### Sample and alignment
# Sample_samplename : test_sample
### Instrument setup
# wavelength_value : 5.0 A
### Scan data
# theta	;	detector	ante_monitor	ante_timer
0.1	;	1.0	100	10.0
### End of test
""")
            f.flush()
            
            scan_file = ScanDataFile(f.name)
            os.unlink(f.name)
            
            result = scan_file.get_dataset('detector', PolarizationEnum.unpolarized)
            assert result is not None
    
    def test_get_dataset_monitor_empty_flippers(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# filepath : /path/to/file.dat
# number : 1
### Experiment information
# Exp_proposal : PROJ1234
# Exp_title : Test
# Exp_users : test_user
### Sample and alignment
# Sample_samplename : test_sample
### Instrument setup
# wavelength_value : 5.0 A
### Scan data
# theta	;	detector	ante_monitor	ante_timer
0.1	;	1.0	100	10.0
### End of test
""")
            f.flush()
            
            scan_file = ScanDataFile(f.name)
            os.unlink(f.name)
            
            result = scan_file.get_dataset_monitor(PolarizationEnum.unpolarized)
            assert result is not None
    
    def test_get_dataset_time_empty_flippers(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write("""### NICOS data file, created at 2024-01-01 12:00:00
# filepath : /path/to/file.dat
# number : 1
### Experiment information
# Exp_proposal : PROJ1234
# Exp_title : Test
# Exp_users : test_user
### Sample and alignment
# Sample_samplename : test_sample
### Instrument setup
# wavelength_value : 5.0 A
### Scan data
# theta	;	detector	ante_monitor	ante_timer
0.1	;	1.0	100	10.0
### End of test
""")
            f.flush()
            
            scan_file = ScanDataFile(f.name)
            os.unlink(f.name)
            
            result = scan_file.get_dataset_time(PolarizationEnum.unpolarized)
            assert result is not None


class TestGetData:
    def test_get_data_nxs(self):
        nxs_path = os.path.join(DATA_DIR, 'GINA_p260209_scan_00000349_theta_twotheta_flipper_1.nxs')
        if not os.path.exists(nxs_path):
            pytest.skip("Nexus file not found")
        
        result = get_data(nxs_path)
        assert result is not None
        assert isinstance(result, NexusFile)

    def test_get_data_dat(self):
        dat_path = os.path.join(DATA_DIR, 'p260209_00000349.dat')
        if not os.path.exists(dat_path):
            pytest.skip("DAT file not found")
        
        result = get_data(dat_path)
        assert result is not None
        assert isinstance(result, ScanDataFile)

    def test_get_data_unknown(self):
        with pytest.raises(ValueError):
            get_data("test.txt")
