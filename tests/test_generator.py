import numpy as np
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
import matplotlib
matplotlib.use('Agg')

from orsopy.fileio import Polarization

from generator.datatypes import (
    EvaluationState,
    ConfigReportInput,
    MainReportInput,
    SummaryReportInput,
    DataReportInput,
    ReportInput,
    Q2M
)
from generator.utils import ideal_reflectivity
from generator.analyser import AnalyserOrso
from generator.report import ReportGenerator


class TestDatatypes:
    def test_evaluation_state(self):
        assert EvaluationState.accepted.value == "Accepted"
        assert EvaluationState.rejected.value == "Rejected"
        assert EvaluationState.special.value == "Note"

    def test_config_report_input_defaults(self):
        config = ConfigReportInput()
        assert config.M_ref == 6.2
        assert config.R_ref == 0.6
        assert config.R_div_max == 0.1
        assert config.M_max == 6.2
        assert config.alpha_spec == 0.075
        assert config.alpha_max == 0.075
        assert config.fit_alfa is True
        assert config.P_min == 0.95
        assert config.Q_Pstart == 0.022
        assert config.Q_Pend == pytest.approx(6.2 / Q2M)

    def test_config_report_input_custom(self):
        config = ConfigReportInput(M_ref=5.0, R_ref=0.5, fit_alfa=False)
        assert config.M_ref == 5.0
        assert config.R_ref == 0.5
        assert config.fit_alfa is False

    def test_main_report_input(self):
        main = MainReportInput(
            owner="Test Owner",
            instrument="GINA",
            proposal_id="test123",
            start_date="2026-01-01",
            proposal_name="Test Proposal",
            sample_name="Test Sample",
            sample_size=[1.0, 2.0, 3.0],
            filename="test.ort",
            correction=["correction1", "correction2"]
        )
        assert main.owner == "Test Owner"
        assert main.instrument == "GINA"
        assert main.sample_size == [1.0, 2.0, 3.0]

    def test_summary_report_input_defaults(self):
        summary = SummaryReportInput(evaluation=EvaluationState.accepted)
        assert summary.evaluation == EvaluationState.accepted
        assert summary.alpha == 0
        assert summary.R_m_ref == 1
        assert summary.ref_in_spec is True
        assert summary.pol_in_spec is False

    def test_summary_report_input_custom(self):
        summary = SummaryReportInput(
            evaluation=EvaluationState.rejected,
            alpha=0.05,
            R_m_ref=0.7,
            ref_in_spec=False,
            pol_in_spec=True,
            scale=1.2,
            use_polarisation=True,
            Pmin=0.96,
            Pavg=0.98
        )
        assert summary.evaluation == EvaluationState.rejected
        assert summary.alpha == 0.05
        assert summary.scale == 1.2
        assert summary.use_polarisation is True

    def test_data_report_input(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([0.1, 0.2, 0.3])
        dx = np.array([0.01, 0.01, 0.01])
        dy = np.array([0.02, 0.02, 0.02])
        
        data = DataReportInput(x=x, y=y, dx=dx, dy=dy, label="test", color="red")
        assert np.array_equal(data.x, x)
        assert np.array_equal(data.y, y)
        assert data.label == "test"
        assert data.color == "red"

    def test_data_report_input_optional(self):
        x = np.array([1.0, 2.0])
        y = np.array([0.1, 0.2])
        dx = np.array([0.01, 0.01])
        dy = np.array([0.02, 0.02])
        
        data = DataReportInput(x=x, y=y, dx=dx, dy=dy)
        assert data.label == ""
        assert data.color is None

    def test_report_input(self):
        config = ConfigReportInput()
        main = MainReportInput(
            owner="Test", instrument="GINA", proposal_id="123",
            start_date="2026-01-01", proposal_name="Test", sample_name="Sample",
            sample_size=[1.0], filename="test.ort", correction=[]
        )
        summary = SummaryReportInput(evaluation=EvaluationState.accepted)
        x = np.array([1.0, 2.0])
        y = np.array([0.1, 0.2])
        dx = np.array([0.01, 0.01])
        dy = np.array([0.02, 0.02])
        data = DataReportInput(x=x, y=y, dx=dx, dy=dy)
        polar = DataReportInput(x=x, y=y, dx=dx, dy=dy, label="pol")
        
        report = ReportInput(
            main=main, summary=summary, data=[data],
            polarisation=polar, config=config, polar_pos={}
        )
        assert report.main.owner == "Test"
        assert len(report.data) == 1


class TestUtils:
    def test_ideal_reflectivity_m_less_than_1(self):
        m = np.array([0.5, 0.8, 0.9])
        result = ideal_reflectivity(m, scale=1.0, alpha=0.075, m_max=6.2)
        np.testing.assert_array_equal(result, np.array([1.0, 1.0, 1.0]))

    def test_ideal_reflectivity_1_to_m_max(self):
        m = np.array([1.0, 2.0, 3.0])
        result = ideal_reflectivity(m, scale=1.0, alpha=0.075, m_max=6.2)
        expected = np.array([1.0, 1.0 - (2.0 - 1.0) * 0.075, 1.0 - (3.0 - 1.0) * 0.075])
        np.testing.assert_array_almost_equal(result, expected)

    def test_ideal_reflectivity_above_m_max(self):
        m = np.array([6.0, 6.2, 7.0, 10.0])
        result = ideal_reflectivity(m, scale=1.0, alpha=0.075, m_max=6.2)
        expected = np.array([1.0 - (6.0 - 1.0) * 0.075, 1.0 - (6.2 - 1.0) * 0.075, 0.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_ideal_reflectivity_with_scale(self):
        m = np.array([2.0])
        result = ideal_reflectivity(m, scale=2.0, alpha=0.075, m_max=6.2)
        expected = 2.0 * (1.0 - (2.0 - 1.0) * 0.075)
        np.testing.assert_array_almost_equal(result, np.array([expected]))

    def test_ideal_reflectivity_scalar(self):
        result = ideal_reflectivity(2.0, 1.0, 0.075, 6.2)
        expected = 1.0 - (2.0 - 1.0) * 0.075
        assert result == pytest.approx(expected)


class TestAnalyserOrso:
    @pytest.fixture
    def mock_file_data(self):
        mock_dataset = Mock()
        mock_dataset.data = np.column_stack([
            np.linspace(0.01, 0.1, 50),
            np.zeros(50),
            np.linspace(0.5, 0.01, 50),
            np.ones(50) * 0.01
        ])
        
        mock_info = Mock()
        mock_sample = Mock()
        mock_sample.name = "Test Sample"
        mock_sample.size = Mock(x=10.0, y=20.0, z=30.0)
        
        mock_experiment = Mock()
        mock_experiment.instrument = "GINA"
        mock_experiment.proposalID = "test123"
        mock_experiment.title = "Test Proposal"
        mock_experiment.start_date = Mock(strftime=lambda fmt: "2026-01-01")
        
        mock_owner = Mock()
        mock_owner.name = "Test Owner"
        
        mock_measurement = Mock()
        mock_settings = Mock()
        mock_settings.polarization = "po"
        mock_measurement.instrument_settings = mock_settings
        
        mock_info.data_source = Mock()
        mock_info.data_source.sample = mock_sample
        mock_info.data_source.experiment = mock_experiment
        mock_info.data_source.owner = mock_owner
        mock_info.data_source.measurement = mock_measurement
        mock_info.reduction = Mock()
        mock_info.reduction.corrections = ["correction1"]
        
        mock_dataset.info = mock_info
        
        return [mock_dataset]

    @pytest.fixture
    def config(self):
        return ConfigReportInput(
            M_ref=6.2,
            R_ref=0.6,
            R_div_max=0.1,
            M_max=6.2,
            alpha_spec=0.075,
            alpha_max=0.075,
            fit_alfa=True,
            P_min=0.95,
            Q_Pstart=0.022,
            Q_Pend=6.2 / Q2M
        )

    def test_init(self, mock_file_data, config):
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            assert analyser.config == config

    def test_main_property(self, mock_file_data, config):
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            main = analyser.main
            assert main.sample_name == "Test Sample"
            assert main.instrument == "GINA"
            assert main.proposal_id == "test123"

    def test_dataset_property(self, mock_file_data, config):
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            dataset = analyser.dataset
            assert len(dataset) == 1

    def test_polar_pos_property(self, mock_file_data, config):
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            polar_pos = analyser.polar_pos
            assert len(polar_pos) > 0

    def test_get_scale_and_alpha_fit_alfa_true(self, mock_file_data, config):
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            
            x = np.linspace(0.01, 0.1, 50)
            y = np.linspace(0.5, 0.01, 50)
            dy = np.ones(50) * 0.01
            data = DataReportInput(x=x, y=y, dx=np.zeros(50), dy=dy)
            
            scale, alpha = AnalyserOrso.get_scale_and_alpha(data, config)
            assert isinstance(scale, (float, np.floating))
            assert isinstance(alpha, (float, np.floating))

    def test_get_scale_and_alpha_fit_alfa_false(self, mock_file_data, config):
        config.fit_alfa = False
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            
            x = np.linspace(0.01, 0.1, 50)
            y = np.linspace(0.5, 0.01, 50)
            dy = np.ones(50) * 0.01
            data = DataReportInput(x=x, y=y, dx=np.zeros(50), dy=dy)
            
            scale, alpha = AnalyserOrso.get_scale_and_alpha(data, config)
            assert isinstance(scale, (float, np.floating))
            assert isinstance(alpha, (float, np.floating))

    def test_get_refl_spec(self, mock_file_data, config):
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            
            x = np.linspace(0.01, 0.2, 50)
            y = np.linspace(0.5, 0.01, 50)
            dy = np.ones(50) * 0.01
            data = DataReportInput(x=x, y=y, dx=np.zeros(50), dy=dy)
            
            R_m_ref, R_div_max = AnalyserOrso.get_refl_spec(data, config)
            assert isinstance(R_m_ref, (float, np.floating))
            assert R_m_ref > 0
            assert isinstance(R_div_max, (float, np.floating))

    def test_get_refl_spec_edge_cases(self, mock_file_data, config):
        x = np.linspace(0.01, 0.2, 50)
        y = np.linspace(0.5, 0.01, 50)
        dy = np.ones(50) * 0.01
        data = DataReportInput(x=x, y=y, dx=np.zeros(50), dy=dy)
        
        R_m_ref, R_div_max = AnalyserOrso.get_refl_spec(data, config)
        assert isinstance(R_m_ref, (float, np.floating))

    def test_polarisation_property_no_polarization(self, mock_file_data, config):
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            pol = analyser.polarisation
            assert pol.label == "polarization"

    def test_summary_property(self, mock_file_data, config):
        mock_info = mock_file_data[0].info
        mock_info.data_source.measurement.instrument_settings.polarization = "po"
        
        mock_dataset2 = Mock()
        mock_dataset2.data = mock_file_data[0].data.copy()
        mock_dataset2.info = mock_info
        
        with patch('generator.analyser.fileio.load_orso', return_value=[mock_dataset2]):
            analyser = AnalyserOrso("test.ort", config)
            summary = analyser.summary
            assert summary.evaluation in [EvaluationState.accepted, EvaluationState.rejected]

    def test_result_property(self, mock_file_data, config):
        with patch('generator.analyser.fileio.load_orso', return_value=mock_file_data):
            analyser = AnalyserOrso("test.ort", config)
            result = analyser.result
            assert isinstance(result, ReportInput)


class TestReportGenerator:
    @pytest.fixture
    def report_input(self):
        config = ConfigReportInput()
        main = MainReportInput(
            owner="Test Owner",
            instrument="GINA",
            proposal_id="test123",
            start_date="2026-01-01",
            proposal_name="Test Proposal",
            sample_name="Test Sample",
            sample_size=[1.0, 2.0, 3.0],
            filename="test.ort",
            correction=["correction1", "correction2"]
        )
        
        x = np.linspace(0.01, 0.1, 50)
        y = np.linspace(0.5, 0.01, 50)
        dx = np.zeros(50)
        dy = np.ones(50) * 0.01
        
        data = DataReportInput(x=x, y=y, dx=dx, dy=dy, label="spin-up", color="blue")
        polar = DataReportInput(x=x, y=y * 0.9, dx=dx, dy=dy * 0.1, label="polarization", color="green")
        
        summary = SummaryReportInput(
            evaluation=EvaluationState.accepted,
            alpha=0.075,
            R_m_ref=0.6,
            R_div_max=0.05,
            ref_in_spec=True,
            pol_in_spec=True,
            scale=1.0,
            use_polarisation=True,
            Pmin=0.96,
            Pavg=0.98
        )
        
        return ReportInput(
            main=main,
            summary=summary,
            data=[data],
            polarisation=polar,
            config=config,
            polar_pos={Polarization.po: 0}
        )

    def test_init_with_polarization(self, report_input):
        report_input.summary.use_polarisation = True
        generator = ReportGenerator(report_input)
        assert generator.fig is not None
        assert generator.result == report_input

    def test_init_without_polarization(self, report_input):
        report_input.summary.use_polarisation = False
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_get_figure(self, report_input):
        generator = ReportGenerator(report_input)
        fig = generator.get_figure()
        assert fig is not None

    def test_savepdf(self, report_input, tmp_path):
        report_input.main.filename = "test_report.ort"
        generator = ReportGenerator(report_input)
        output_file = tmp_path / "test.pdf"
        generator.savepdf(str(output_file))
        assert output_file.exists()

    def test_savepdf_none_filename(self, report_input):
        report_input.main.filename = "test_report.ort"
        generator = ReportGenerator(report_input)
        generator.savepdf(None)

    @patch('generator.report.plt.show')
    def test_show(self, mock_show, report_input):
        generator = ReportGenerator(report_input)
        generator.show()
        mock_show.assert_called_once()

    def test_draw_evaluation_accepted(self, report_input):
        report_input.summary.evaluation = EvaluationState.accepted
        report_input.summary.ref_in_spec = True
        report_input.summary.pol_in_spec = True
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_draw_evaluation_rejected(self, report_input):
        report_input.summary.evaluation = EvaluationState.rejected
        report_input.summary.ref_in_spec = False
        report_input.summary.pol_in_spec = False
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_draw_evaluation_special(self, report_input):
        report_input.summary.evaluation = EvaluationState.special
        report_input.summary.ref_in_spec = False
        report_input.summary.pol_in_spec = False
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_plot_reflectivity_multiple_datasets(self, report_input):
        x = np.linspace(0.01, 0.1, 50)
        y = np.linspace(0.5, 0.01, 50)
        dx = np.zeros(50)
        dy = np.ones(50) * 0.01
        
        data2 = DataReportInput(x=x, y=y * 0.8, dx=dx, dy=dy, label="spin-down", color="red")
        report_input.data.append(data2)
        
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_plot_corrected_reflectivity_with_polarization(self, report_input):
        report_input.summary.use_polarisation = True
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_plot_corrected_reflectivity_without_polarization(self, report_input):
        report_input.summary.use_polarisation = False
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_plot_polarization(self, report_input):
        report_input.summary.use_polarisation = True
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_plot_polarization_below_spec(self, report_input):
        report_input.summary.use_polarisation = True
        report_input.polarisation = DataReportInput(
            x=np.linspace(0.01, 0.1, 10),
            y=np.array([0.8, 0.85, 0.9, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]),
            dx=np.zeros(10),
            dy=np.ones(10) * 0.01,
            label="polarization",
            color="green"
        )
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_draw_parameters(self, report_input):
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_draw_parameters_many_corrections(self, report_input):
        report_input.main.correction = [f"correction_{i}" for i in range(20)]
        generator = ReportGenerator(report_input)
        assert generator.fig is not None

    def test_plot_reflectivity_with_r_up_less_than_ref(self, report_input):
        x = np.linspace(0.01, 0.1, 50)
        y = np.ones(50) * 0.001
        dx = np.zeros(50)
        dy = np.ones(50) * 0.0001
        
        data = DataReportInput(x=x, y=y, dx=dx, dy=dy, label="spin-up", color="blue")
        report_input.data = [data]
        
        generator = ReportGenerator(report_input)
        assert generator.fig is not None


class TestAnalyserOrsoWithPolarization:
    @pytest.fixture
    def mock_polarized_data(self):
        mock_dataset_po = Mock()
        mock_dataset_po.data = np.column_stack([
            np.linspace(0.01, 0.1, 50),
            np.zeros(50),
            np.linspace(0.5, 0.01, 50),
            np.ones(50) * 0.01
        ])
        
        mock_info = Mock()
        mock_sample = Mock()
        mock_sample.name = "Test Sample"
        mock_sample.size = Mock(x=10.0, y=20.0, z=30.0)
        
        mock_experiment = Mock()
        mock_experiment.instrument = "GINA"
        mock_experiment.proposalID = "test123"
        mock_experiment.title = "Test Proposal"
        mock_experiment.start_date = Mock(strftime=lambda fmt: "2026-01-01")
        
        mock_owner = Mock()
        mock_owner.name = "Test Owner"
        
        mock_measurement = Mock()
        mock_settings = Mock()
        
        mock_settings_po = Mock()
        mock_settings_po.polarization = "po"
        mock_settings_mo = Mock()
        mock_settings_mo.polarization = "mo"
        
        mock_measurement.instrument_settings = mock_settings_po
        
        mock_info.data_source = Mock()
        mock_info.data_source.sample = mock_sample
        mock_info.data_source.experiment = mock_experiment
        mock_info.data_source.owner = mock_owner
        mock_info.data_source.measurement = mock_measurement
        mock_info.reduction = Mock()
        mock_info.reduction.corrections = ["correction1"]
        
        mock_dataset_po.info = mock_info
        
        mock_dataset_mo = Mock()
        mock_dataset_mo.data = np.column_stack([
            np.linspace(0.01, 0.1, 50),
            np.zeros(50),
            np.linspace(0.4, 0.008, 50),
            np.ones(50) * 0.01
        ])
        
        mock_info_mo = Mock()
        mock_info_mo.data_source = mock_info.data_source
        mock_info_mo.data_source.measurement = mock_settings_mo
        mock_info_mo.reduction = mock_info.reduction
        
        mock_dataset_mo.info = mock_info_mo
        
        return [mock_dataset_po, mock_dataset_mo]

    def test_polarized_analysis(self, mock_polarized_data, config=None):
        if config is None:
            config = ConfigReportInput(
                M_ref=6.2, R_ref=0.6, R_div_max=0.1,
                M_max=6.2, alpha_spec=0.075, alpha_max=0.075,
                fit_alfa=True, P_min=0.95, Q_Pstart=0.022, Q_Pend=6.2 / Q2M
            )
        
        with patch('generator.analyser.fileio.load_orso', return_value=mock_polarized_data):
            analyser = AnalyserOrso("test.ort", config)
            pol = analyser.polarisation
            assert pol.label == "polarization"
            assert pol.color == "green"
            
            assert len(analyser.polar_pos) >= 1


@pytest.fixture
def config():
    return ConfigReportInput(
        M_ref=6.2,
        R_ref=0.6,
        R_div_max=0.1,
        M_max=6.2,
        alpha_spec=0.075,
        alpha_max=0.075,
        fit_alfa=True,
        P_min=0.95,
        Q_Pstart=0.022,
        Q_Pend=6.2 / Q2M
    )
