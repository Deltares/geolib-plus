import pytest
from typing import List, Dict
import numpy as np
import re
from geolib_plus.gef_cpt.gef_file_reader import GefFileReader, GefProperty
import logging


class TestGefFileReaderInit:
    @pytest.mark.unittest
    def test_when_init_default_properties_are_set(self):
        # Define expected property_dict
        expected_dict = {
            "depth": GefProperty(gef_key=1, multiplication_factor=1.0),
            "tip": GefProperty(gef_key=2, multiplication_factor=1000.0),
            "friction": GefProperty(gef_key=3, multiplication_factor=1000.0),
            "friction_nb": GefProperty(gef_key=4, multiplication_factor=1.0),
            "pwp": GefProperty(gef_key=6, multiplication_factor=1000.0),
        }
        file_reader = GefFileReader()
        assert file_reader.name == ""
        assert file_reader.coord == []
        assert isinstance(file_reader.property_dict, dict)
        assert file_reader.__eq__(expected_dict)


class TestGetLineIndexFromData:
    @pytest.mark.unittest
    @pytest.mark.xfail(raises=ValueError)
    @pytest.mark.parametrize(
        "code_string, data, expectation",
        [
            (None, None, pytest.raises(ValueError)),
            (None, [], pytest.raises(ValueError)),
            (None, ["alpha"], pytest.raises(ValueError)),
            ("alpha", None, pytest.raises(ValueError)),
            ("alpha", [], pytest.raises(ValueError)),
            ("alpha", ["beta"], pytest.raises(ValueError)),
        ],
    )
    def test_given_test_case_arguments_then_raises_exception(
        self, code_string: str, data: List[str], expectation
    ):
        with expectation:
            GefFileReader.get_line_index_from_data(code_string, data)

    def test_given_valid_arguments_then_returns_expected_line(self):
        # 1. Define test data
        code_string = "beta"
        data = ["24 42 beta", "42 24 alpha", "alpha 42 24", "beta 24 42"]
        expected_result = 3

        # 2. Run test
        result = GefFileReader.get_line_index_from_data(code_string, data)

        # 3. Validate final expectation
        assert result == expected_result


class TestGefUtil:
    @pytest.mark.unittest
    def test_correct_negatives_and_zeros(self):
        # initialise model
        gef_reader = GefFileReader()
        # define keys that cannot be zero
        list_non_zero = ["depth"]
        gef_reader.property_dict["depth"].gef_column_index = 1
        gef_reader.property_dict["tip"].gef_column_index = 2
        gef_reader.property_dict["depth"].values_from_gef = [-1, -2, -9]
        gef_reader.property_dict["tip"].values_from_gef = [-1, -2, -9]
        # run the test
        gef_reader.correct_negatives_and_zeros(correct_for_negatives=list_non_zero)
        # check the output
        assert (
            gef_reader.property_dict["depth"].values_from_gef == np.array([0, 0, 0])
        ).all()
        assert gef_reader.property_dict["tip"].values_from_gef == [-1, -2, -9]

    @pytest.mark.systemtest
    def test_read_data_no_pore_pressure(self):
        # initialise model
        gef_reader = GefFileReader()
        gef_reader.property_dict["depth"].gef_column_index = 0
        gef_reader.property_dict["friction"].gef_column_index = 2
        gef_reader.property_dict["tip"].gef_column_index = 1
        gef_reader.property_dict["pwp"].gef_column_index = None
        gef_reader.property_dict["friction_nb"].gef_column_index = 5
        # read gef file
        gef_file = ".\\tests\\test_files\\cpt\\gef\\unit_testing\\test_read_data.gef"
        with open(gef_file, "r") as f:
            data = f.readlines()
        idx_EOH = [i for i, val in enumerate(data) if val.startswith(r"#EOH=")][0]
        data[idx_EOH + 1 :] = [
            re.sub("[ :,!\t]+", ";", i.lstrip()) for i in data[idx_EOH + 1 :]
        ]
        # Run test
        gef_reader.read_data(data, idx_EOH)
        # Check output
        assert gef_reader.property_dict["depth"].values_from_gef[-1] == 25.61
        assert gef_reader.property_dict["tip"].values_from_gef[-1] == 13387.0
        assert gef_reader.property_dict["friction"].values_from_gef[-1] == -99999000.0
        assert gef_reader.property_dict["pwp"].values_from_gef[-1] == 0.0

    @pytest.mark.systemtest
    def test_read_data_error_raised(self):
        # depth input was not find in the cpt file
        # initialise model
        gef_reader = GefFileReader()
        gef_reader.property_dict["depth"].gef_column_index = None
        gef_reader.property_dict["friction"].gef_column_index = 2
        gef_reader.property_dict["tip"].gef_column_index = 1
        gef_reader.property_dict["pwp"].gef_column_index = None
        gef_reader.property_dict["friction_nb"].gef_column_index = 5
        # read gef file
        gef_file = ".\\tests\\test_files\\cpt\\gef\\unit_testing\\test_read_data.gef"
        with open(gef_file, "r") as f:
            data = f.readlines()
        idx_EOH = [i for i, val in enumerate(data) if val.startswith(r"#EOH=")][0]
        data[idx_EOH + 1 :] = [
            re.sub("[ :,!\t]+", ";", i.lstrip()) for i in data[idx_EOH + 1 :]
        ]
        # Run test

        with pytest.raises(Exception) as excinfo:
            gef_reader.read_data(data, idx_EOH)
        assert "CPT key: depth not part of GEF file" == str(excinfo.value)

    @pytest.mark.unittest
    def test_remove_points_with_error(self):
        # initialise model
        gef_reader = GefFileReader()
        # set inputs
        gef_reader.property_dict["depth"].values_from_gef = np.linspace(2, 20, 6)
        gef_reader.property_dict["friction"].values_from_gef = np.array(
            [-1, -2, -999, -999, -3, -4]
        )
        gef_reader.property_dict["pwp"].values_from_gef = np.full(6, 1000)
        gef_reader.property_dict["friction_nb"].values_from_gef = np.full(6, 5)

        gef_reader.property_dict["depth"].error_code = -1
        gef_reader.property_dict["friction"].error_code = -999
        gef_reader.property_dict["pwp"].error_code = -1
        gef_reader.property_dict["friction_nb"].error_code = -1

        gef_reader.property_dict["depth"].gef_column_index = 4
        gef_reader.property_dict["friction"].gef_column_index = 2
        gef_reader.property_dict["tip"].gef_column_index = 1
        gef_reader.property_dict["pwp"].gef_column_index = 3
        gef_reader.property_dict["friction_nb"].gef_column_index = 5

        # initialise the model
        gef_reader.remove_points_with_error()
        assert (
            gef_reader.property_dict["friction"].values_from_gef
            == np.array([-1, -2, -3, -4])
        ).all()
        assert (
            gef_reader.property_dict["depth"].values_from_gef
            == np.array([2.0, 5.6, 16.4, 20.0])
        ).all()
        assert (
            gef_reader.property_dict["friction_nb"].values_from_gef == np.full(4, 5)
        ).all()
        assert (
            gef_reader.property_dict["pwp"].values_from_gef == np.full(4, 1000)
        ).all()

    @pytest.mark.unittest
    def test_remove_points_with_error_raises(self):
        # value pwp size is minimized to raise error
        # initialise model
        gef_reader = GefFileReader()
        # set inputs
        gef_reader.property_dict["depth"].values_from_gef = np.linspace(2, 20, 6)
        gef_reader.property_dict["friction"].values_from_gef = np.array(
            [-1, -2, -3, -4, -999, -999]
        )
        gef_reader.property_dict["pwp"].values_from_gef = np.full(5, 1000)
        gef_reader.property_dict["friction_nb"].values_from_gef = np.full(6, 5)

        gef_reader.property_dict["depth"].error_code = -1
        gef_reader.property_dict["friction"].error_code = -999
        gef_reader.property_dict["pwp"].error_code = -1
        gef_reader.property_dict["friction_nb"].error_code = -1

        gef_reader.property_dict["depth"].gef_column_index = 4
        gef_reader.property_dict["friction"].gef_column_index = 2
        gef_reader.property_dict["tip"].gef_column_index = 1
        gef_reader.property_dict["pwp"].gef_column_index = 3
        gef_reader.property_dict["friction_nb"].gef_column_index = 5
        # Run test
        with pytest.raises(Exception) as excinfo:
            gef_reader.remove_points_with_error()
        assert "Index <4> excides the length of list of key 'pwp'" == str(excinfo.value)

    @pytest.mark.unittest
    def test_read_column_index_for_gef_data(self):
        # define all inputs
        doc_snippet = [
            "#COLUMN= 10",
            "#COLUMNINFO= 1, m, Sondeerlengte, 1",
            "#COLUMNINFO= 2, MPa, Conusweerstand qc, 2",
            "#COLUMNINFO= 3, MPa, Wrijvingsweerstand fs, 3",
            "#COLUMNINFO= 4, %, Wrijvingsgetal Rf, 4",
            "#COLUMNINFO= 5, MPa, Waterspanning u2, 6",
            "#COLUMNINFO= 6, graden, Helling X, 21",
            "#COLUMNINFO= 7, graden, Helling Y, 22",
            "#COLUMNINFO= 8, -, Classificatie zone Robertson 1990, 99",
            "#COLUMNINFO= 9, m, Gecorrigeerde diepte, 11",
            "#COLUMNINFO= 10, s, Tijd, 12",
        ]
        # indexes that match columns in gef file
        indexes = [1, 2, 3, 4, 6, 21, 22, 99, 11, 12]
        # initialise the model
        gef_reader = GefFileReader()
        # Run the test
        for counter, index in enumerate(indexes):
            assert counter == gef_reader.read_column_index_for_gef_data(
                key_cpt=index, data=doc_snippet
            )

    @pytest.mark.unittest
    def test_read_column_index_for_gef_data_error(self):
        # define all inputs
        doc_snippet = [
            "#COLUMN= 10",
            "#COLUMNINFO= 1, m, Sondeerlengte, 1",
            "#COLUMNINFO= 2, MPa, Conusweerstand qc, 2",
            "#COLUMNINFO= 3, MPa, Wrijvingsweerstand fs, 3",
            "#COLUMNINFO= 4, %, Wrijvingsgetal Rf, 4",
            "#COLUMNINFO= 5, MPa, Waterspanning u2, 6",
            "#COLUMNINFO= 6, graden, Helling X, 21",
            "#COLUMNINFO= 7, graden, Helling Y, 22",
            "#COLUMNINFO= 8, -, Classificatie zone Robertson 1990, 99",
            "#COLUMNINFO= 9, m, Gecorrigeerde diepte, 11",
            "#COLUMNINFO= 10, s, Tijd, 12",
        ]
        # indexes don't match the columns in gef file
        index = 5
        # initialise the model
        gef_reader = GefFileReader()
        # Run the test
        assert not (
            gef_reader.read_column_index_for_gef_data(key_cpt=index, data=doc_snippet)
        )

    @pytest.mark.unittest
    def test_match_idx_with_error(self):
        # Set the inputs
        error_string_list = [
            "-1",
            "-2",
            "-3",
            "string",
            "-5",
            "string",
            "-7",
            "-8",
            "-9",
            "-10",
        ]
        # initialise model
        gef_reader = GefFileReader()
        # set inputs
        gef_reader.property_dict["depth"].gef_key = 0
        gef_reader.property_dict["tip"].gef_key = 1
        gef_reader.property_dict["friction"].gef_key = 2
        gef_reader.property_dict["pwp"].gef_key = 4
        gef_reader.property_dict["friction_nb"].gef_key = 3

        gef_reader.property_dict["depth"].multiplication_factor = 1
        gef_reader.property_dict["friction"].multiplication_factor = 1000
        gef_reader.property_dict["pwp"].multiplication_factor = 1000
        gef_reader.property_dict["friction_nb"].multiplication_factor = 1000

        gef_reader.property_dict["depth"].gef_column_index = 4
        gef_reader.property_dict["friction"].gef_column_index = 2
        gef_reader.property_dict["tip"].gef_column_index = 1
        gef_reader.property_dict["pwp"].gef_column_index = 3
        gef_reader.property_dict["friction_nb"].gef_column_index = 5

        # Run test
        gef_reader.match_idx_with_error(error_string_list)
        # Check expectations
        assert gef_reader.property_dict["depth"].error_code == -5
        assert gef_reader.property_dict["tip"].error_code == -2 * 1000
        assert gef_reader.property_dict["friction"].error_code == -3 * 1000
        assert gef_reader.property_dict["friction_nb"].error_code == "string"
        assert gef_reader.property_dict["pwp"].error_code == "string"

    @pytest.mark.unittest
    def test_match_idx_with_error_raises_1(self):
        # Set the inputs. One value is missing from the list
        error_string_list = ["-1", "-2", "-3", "string", "-4"]

        # initialise model
        gef_reader = GefFileReader()
        gef_reader.property_dict["depth"].multiplication_factor = 1
        gef_reader.property_dict["friction"].multiplication_factor = 1000
        gef_reader.property_dict["pwp"].multiplication_factor = 1000
        gef_reader.property_dict["friction_nb"].multiplication_factor = 1000

        gef_reader.property_dict["depth"].gef_column_index = 4
        gef_reader.property_dict["friction"].gef_column_index = 2
        gef_reader.property_dict["tip"].gef_column_index = None
        gef_reader.property_dict["pwp"].gef_column_index = 3
        gef_reader.property_dict["friction_nb"].gef_column_index = 5
        # Run test
        with pytest.raises(Exception) as excinfo:
            gef_reader.match_idx_with_error(error_string_list)
        assert "Key tip should be defined in the gef file" in str(excinfo.value)

    @pytest.mark.intergration
    def test_read_gef_1(self):
        gef_file = "./tests/test_files/cpt/gef/unit_testing/unit_testing.gef"

        # initialise the model
        gef_reader = GefFileReader()
        # run the test
        cpt = gef_reader.read_gef(gef_file=gef_file)
        test_coord = [244319.00, 587520.00]

        test_depth = np.linspace(1, 20, 20)
        test_NAP = -1 * test_depth + 0.13
        test_tip = np.full(20, 1000)
        test_friction = np.full(20, 2000)
        test_friction_nbr = np.full(20, 5)
        test_water = np.full(20, 3000)

        assert "DKP302" == cpt["name"]
        assert test_coord == cpt["coordinates"]
        assert (test_depth == cpt["depth"]).all()
        assert (test_NAP == cpt["depth_to_reference"]).all()
        assert (test_tip == cpt["tip"]).all()
        assert (test_friction == cpt["friction"]).all()
        assert (test_friction_nbr == cpt["friction_nbr"]).all()
        assert (test_water == cpt["water"]).all()

    @pytest.mark.intergration
    @pytest.mark.parametrize(
        "filename, error",
        [
            pytest.param(
                "./tests/test_files/cpt/gef/unit_testing/Exception_NoLength.gef",
                "Key depth should be defined in the gef file.",
                id="no depth",
            ),
            pytest.param(
                "./tests/test_files/cpt/gef/unit_testing/Exception_NoTip.gef",
                "Key tip should be defined in the gef file.",
                id="no tip",
            ),
        ],
    )
    def test_read_gef_missing_field_error(self, filename: str, error: str):
        # initialise the model
        gef_reader = GefFileReader()
        # test exceptions
        with pytest.raises(Exception) as excinfo:
            gef_reader.read_gef(gef_file=filename)
        assert error == str(excinfo.value)

    @pytest.mark.intergration
    @pytest.mark.parametrize(
        "filename, warning",
        [
            pytest.param(
                "./tests/test_files/cpt/gef/unit_testing/Exception_NoFriction.gef",
                "Key friction is not defined in the gef file",
                id="no friction",
            ),
            pytest.param(
                "./tests/test_files/cpt/gef/unit_testing/Exception_NoFrictionNumber.gef",
                "Key friction is not defined in the gef file",
                id="no num",
            ),
        ],
    )
    def test_read_gef_missing_field_warning(self, filename: str, warning: str, caplog):
        LOGGER = logging.getLogger(__name__)
        # define logger
        LOGGER.info("Testing now.")
        # initialise the model
        gef_reader = GefFileReader()
        # test exceptions
        result_dictionary = gef_reader.read_gef(gef_file=filename)
        assert warning in caplog.text

    @pytest.mark.intergration
    def test_read_gef_3(self):
        filename = "./tests/test_files/cpt/gef/unit_testing/Exception_9999.gef"

        # initialise the model
        gef_reader = GefFileReader()
        # run the test
        cpt = gef_reader.read_gef(gef_file=filename)

        # define tests
        test_coord = [244319.00, 587520.00]
        test_depth = np.linspace(2, 20, 19)
        test_NAP = -1 * test_depth + 0.13
        test_tip = np.full(19, 1000)
        test_friction = np.full(19, 2000)
        test_friction_nbr = np.full(19, 5)
        test_water = np.full(19, 3000)

        # test expectations
        assert "DKP302" == cpt["name"]
        assert test_coord == cpt["coordinates"]
        assert (test_depth == cpt["depth"]).all()
        assert (test_NAP == cpt["depth_to_reference"]).all()
        assert (test_tip == cpt["tip"]).all()
        assert (test_friction == cpt["friction"]).all()
        assert (test_friction_nbr == cpt["friction_nbr"]).all()
        assert (test_water == cpt["water"]).all()

    @pytest.mark.unittest
    def test_read_data(self):

        # initialise model
        gef_reader = GefFileReader()
        # set inputs
        gef_reader.property_dict["depth"].multiplication_factor = 1
        gef_reader.property_dict["friction"].multiplication_factor = 1000
        gef_reader.property_dict["pwp"].multiplication_factor = 1000
        gef_reader.property_dict["friction_nb"].multiplication_factor = 1000

        gef_reader.property_dict["depth"].gef_column_index = 0
        gef_reader.property_dict["friction"].gef_column_index = 2
        gef_reader.property_dict["tip"].gef_column_index = 1
        gef_reader.property_dict["pwp"].gef_column_index = 3
        gef_reader.property_dict["friction_nb"].gef_column_index = 5

        # read gef file
        gef_file = ".\\tests\\test_files\\cpt\\gef\\unit_testing\\test_read_data.gef"
        with open(gef_file, "r") as f:
            data = f.readlines()
        idx_EOH = [i for i, val in enumerate(data) if val.startswith(r"#EOH=")][0]
        data[idx_EOH + 1 :] = [
            re.sub("[ :,!\t]+", ";", i.lstrip()) for i in data[idx_EOH + 1 :]
        ]

        # Run test
        gef_reader.read_data(data, idx_EOH)
        # Check output
        assert gef_reader.property_dict["depth"].values_from_gef[-1] == 25.61
        assert gef_reader.property_dict["tip"].values_from_gef[-1] == 13387.0
        assert gef_reader.property_dict["friction"].values_from_gef[-1] == -99999000.0
        assert gef_reader.property_dict["pwp"].values_from_gef[-1] == -99999000.0

    @pytest.mark.unittest
    def test_get_line_index_from_data(self):
        # set inputs
        data = [
            "#SPECIMENVAR=  1 ,   0.00, m, ",
            "#TESTID= DKMP1_1317-0162-000",
            "#REPORTCODE= GEF-CPT-Report,1,1,0",
            "#STARTDATE= 2017,07,03",
            "#STARTTIME= 14,13,53",
            "#OS= DOS",
        ]
        code_string = r"#STARTDATE="
        # run test
        test_id = GefFileReader.get_line_index_from_data(
            code_string=code_string, data=data
        )
        assert test_id == 3

    @pytest.mark.unittest
    def test_get_line_index_from_data_error(self):
        # set inputs
        data = [
            "#SPECIMENVAR=  1 ,   0.00, m, ",
            "#TESTID= DKMP1_1317-0162-000",
            "#REPORTCODE= GEF-CPT-Report,1,1,0",
            "#STARTDATE= 2017,07,03",
            "#STARTTIME= 14,13,53",
            "#OS= DOS",
        ]
        code_string = r"#IAMNOTINTHEFILE="
        # Run test
        with pytest.raises(ValueError) as excinfo:
            GefFileReader.get_line_index_from_data(code_string=code_string, data=data)
        assert "No values found for field #IAMNOTINTHEFILE= of the gef file." in str(
            excinfo.value
        )
