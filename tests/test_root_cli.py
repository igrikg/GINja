import argparse
import pytest
from unittest.mock import Mock, patch
import sys
import importlib.util


def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestConverter:
    def test_add_dataclass_to_group_basic(self):
        from converter import DataSourceConfig
        converter_cli = load_module_from_path('converter_cli', 'converter.py')
        
        parser = argparse.ArgumentParser()
        converter_cli.add_dataclass_to_group(parser, DataSourceConfig, "Test Group", "test_")
        args = parser.parse_args([])
        assert hasattr(args, 'test_detector')

    def test_parse_args_to_dataclass_basic(self):
        from converter import DataSourceConfig
        converter_cli = load_module_from_path('converter_cli', 'converter.py')
        
        parser = argparse.ArgumentParser()
        converter_cli.add_dataclass_to_group(parser, DataSourceConfig, "Test Group", "test_")
        args = parser.parse_args(['--test_detector', 'detector1'])
        result = converter_cli.parse_args_to_dataclass(args, DataSourceConfig, "test_")
        assert result.detector == 'detector1'

    def test_main_missing_filename(self):
        converter_cli = load_module_from_path('converter_cli', 'converter.py')
        with patch.object(sys, 'argv', ['converter']):
            with pytest.raises(SystemExit):
                converter_cli.main()


class TestNobTypeConverter:
    def test_main_missing_args(self):
        import nob_type_converter
        with patch.object(sys, 'argv', ['nob_type_converter']):
            with pytest.raises(SystemExit):
                nob_type_converter.main()

    def test_main_missing_detector(self):
        import nob_type_converter
        with patch.object(sys, 'argv', ['nob_type_converter', 'test.nxs']):
            with pytest.raises(SystemExit):
                nob_type_converter.main()


class TestGinjaReportCliMissingArgs:
    def test_main_missing_args(self):
        import ginja_report_cli
        with patch.object(sys, 'argv', ['ginja_report_cli']):
            with pytest.raises(SystemExit):
                ginja_report_cli.main()


class TestReportMissingArgs:
    def test_main_missing_args(self):
        import report
        with patch.object(sys, 'argv', ['report']):
            with pytest.raises(SystemExit):
                report.main()
