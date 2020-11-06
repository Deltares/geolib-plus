"""
BRO XML CPT database reader, indexer and parser.

Enables searching of very large XML CPT database dumps.
In order to speed up these operations, an index will
be created by searching for `featureMember`s (CPTs) in the xml
if it does not yet exist next to the XML file.

The index is stored next to the file and stores the xml
filesize to validate the xml database is the same. If not,
we assume the database is new and a new index will be created
as well. The index itself is an array with columns that store
the x y location of the CPT and the start/end bytes in the XML file.

As of January 2019, almost a 100.000 CPTs are stored in the XML
and creating the index will take 5-10min depending on disk performance.

"""

import logging
from io import StringIO
import pickle
import mmap
from os.path import exists, splitext
from os import stat, name
from zipfile import ZipFile


# External modules
from lxml import etree
import numpy as np
from scipy.spatial import cKDTree as KDTree
import pandas as pd
import pyproj
from lxml.etree import _Element
from pathlib import Path
from typing import Dict, List, Union, Iterable, Optional
from pydantic import BaseModel
from typing import TypeVar

from geolib_plus.cpt_base_model import CptReader
from .validate_bro import validate_bro_cpt

# Types not included in typing
PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")
# Constants for XML parsing
searchstring = b"<gml:featureMember>"
footer = b"</gml:FeatureCollection>"

req_columns = ["penetrationLength", "coneResistance", "localFriction", "frictionRatio"]


ns = "{http://www.broservices.nl/xsd/cptcommon/1.1}"
ns2 = "{http://www.broservices.nl/xsd/dscpt/1.1}"
ns3 = "{http://www.opengis.net/gml/3.2}"
ns4 = "{http://www.broservices.nl/xsd/brocommon/3.0}"
ns5 = "{http://www.opengis.net/om/2.0}"

nodata = -999999
to_epsg = "28992"


def query_index(index, x, y, radius=1000.0):
    """Query database for CPTs
    within radius of x, y.

    :param index: Index is a array with columns: x y begin end
    :type index: np.array
    :param x: X coordinate
    :type x: float
    :param y: Y coordinate
    :type y: float
    :param radius: Radius (m) to use for searching. Defaults to 1000.
    :type radius: float
    :return: 2d array of start/end (columns) for each location (rows).
    :rtype: np.array
    """

    # Setup KDTree based on points
    npindex = np.array(index)
    tree = KDTree(npindex[:, 0:2])

    # Query point and return slices
    points = tree.query_ball_point((float(x), float(y)), float(radius))

    # Return slices
    return npindex[points, 2:4].astype(np.int64)


class XMLBroColumnValues(BaseModel):
    penetrationLength: Union[Iterable, None] = None
    depth: Union[Iterable, None] = None
    elapsedTime: Union[Iterable, None] = None
    coneResistance: Union[Iterable, None] = None
    correctedConeResistance: Union[Iterable, None] = None
    netConeResistance: Union[Iterable, None] = None
    magneticFieldStrengthX: Union[Iterable, None] = None
    magneticFieldStrengthY: Union[Iterable, None] = None
    magneticFieldStrengthZ: Union[Iterable, None] = None
    magneticFieldStrengthTotal: Union[Iterable, None] = None
    electricalConductivity: Union[Iterable, None] = None
    inclinationEW: Union[Iterable, None] = None
    inclinationNS: Union[Iterable, None] = None
    inclinationX: Union[Iterable, None] = None
    inclinationY: Union[Iterable, None] = None
    inclinationResultant: Union[Iterable, None] = None
    magneticInclination: Union[Iterable, None] = None
    magneticDeclination: Union[Iterable, None] = None
    localFriction: Union[Iterable, None] = None
    poreRatio: Union[Iterable, None] = None
    temperature: Union[Iterable, None] = None
    porePressureU1: Union[Iterable, None] = None
    porePressureU2: Union[Iterable, None] = None
    porePressureU3: Union[Iterable, None] = None
    frictionRatio: Union[Iterable, None] = None


class XMLBroFullData(XMLBroColumnValues):
    id: Optional[str]
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    offset_z: Optional[float] = None
    predrilled_z: Optional[float] = None
    a: Optional[float] = 0.80
    vertical_datum: Optional[str]
    local_reference: Optional[str]
    quality_class: Optional[str]
    cone_penetrometer_type: Optional[str]
    cpt_standard: Optional[str]
    result_time: Optional[str]
    dataframe: Optional[PandasDataFrame]

    @property
    def columns_string_list(self):
        return list(dict(XMLBroColumnValues()).keys())


class XMLBroCPTReader(CptReader):
    bro_data: XMLBroFullData = XMLBroFullData()
    water_measurement_type: List = []
    bro_dataframe_map: Dict[str, str] = {
        "penetration_length": "penetrationLength",
        "depth": "depth",
        "time": "elapsedTime",
        "tip": "coneResistance",
        "Qtn": "correctedConeResistance",
        "net_tip": "netConeResistance",
        "magnetic_strength_x": "magneticFieldStrengthX",
        "magnetic_strength_y": "magneticFieldStrengthY",
        "magnetic_strength_z": "magneticFieldStrengthZ",
        "magnetic_strength_tot": "magneticFieldStrengthTotal",
        "electric_cond": "electricalConductivity",
        "inclination_ew": "inclinationEW",
        "inclination_ns": "inclinationNS",
        "inclination_x": "inclinationX",
        "inclination_y": "inclinationY",
        "inclination_resultant": "inclinationResultant",
        "magnetic_inclination": "magneticInclination",
        "magnetic_declination": "magneticDeclination",
        "friction": "localFriction",
        "pore_ratio": "poreRatio",
        "temperature": "temperature",
        "pore_pressure_u1": "porePressureU1",
        "pore_pressure_u2": "porePressureU2",
        "pore_pressure_u3": "porePressureU3",
        "friction_nbr": "frictionRatio",
    }

    @property
    def __water_measurement_types(self):
        return [
            "porePressureU1",
            "porePressureU2",
            "porePressureU3",
        ]

    @staticmethod
    def xml_to_byte_string(fn: Path) -> bytes:
        """
        Opens an xml-file and returns a byte-string
        :param fn: xml file name
        :return: byte-string of the xml file
        """
        ext = splitext(fn)[1]
        if ext == ".xml":
            with open(fn, "r") as f:
                # memory-map the file, size 0 means whole file
                xml_bytes = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)[:]
        return xml_bytes

    def search_values_in_root(self, root: _Element, search_item: str) -> str:
        for loc in root.iter(search_item):
            return loc.text

    def find_availed_data_columns(self, root: _Element) -> List:
        """ Find which columns are not empty. """
        avail_columns = []
        for parameters in root.iter(ns + "parameters"):
            for parameter in parameters:
                if parameter.text == "ja":
                    avail_columns.append(parameter.tag[len(ns) :])
        return avail_columns

    def parse_bro_xml(self, xml: bytes):
        """
        Populates class with xml data. No interpretation of results occurs
        at this function. This is simply reading the xml.
        TODO Replace iter by single search as iter can give multiple results

        :param xml: XML bytes
        """
        root = etree.fromstring(xml)

        # Location
        x, y = self.parse_xml_location(xml)
        self.bro_data.location_x = float(x)
        self.bro_data.location_y = float(y)

        # fill in the data structure from bro
        self.get_all_data_from_bro(root=root)

        # Find which columns are not empty
        avail_columns = self.find_availed_data_columns(root=root)

        # Determine if all data is available
        self.are_all_required_data_available(avail_columns=avail_columns)

        # Parse data array, replace nodata, filter and sort
        for cpt in root.iter(ns + "conePenetrationTest"):
            for element in cpt.iter(ns + "values"):
                # Load string data and parse as 2d array
                sar = StringIO(element.text.replace(";", "\n"))
                array_data = np.loadtxt(sar, delimiter=",", ndmin=2)

                # Check shape of array
                found_rows, found_columns = array_data.shape
                if found_columns != len(self.bro_data.columns_string_list):
                    logging.warning(
                        "Data has the wrong size! {} columns instead of {}".format(
                            found_columns, len(self.bro_data.columns_string_list)
                        )
                    )
                    return

                # Replace nodata constant with nan
                # Create a DataFrame from array
                # and sort by depth
                array_data[array_data == nodata] = np.nan
                df = pd.DataFrame(array_data, columns=self.bro_data.columns_string_list)
                df = df[avail_columns]
                df.sort_values(by=["penetrationLength"], inplace=True)

            self.bro_data.dataframe = df

    def all_single_data_available(self) -> bool:
        return None not in [
            self.bro_data.id,
            self.bro_data.location_x,
            self.bro_data.location_y,
            self.bro_data.offset_z,
            self.bro_data.predrilled_z,
            self.bro_data.a,
            self.bro_data.vertical_datum,
            self.bro_data.local_reference,
            self.bro_data.quality_class,
            self.bro_data.cone_penetrometer_type,
            self.bro_data.cpt_standard,
            self.bro_data.result_time,
        ]

    def are_all_required_data_available(self, avail_columns: List) -> None:
        """ Determine if all data is available """
        meta_usable = self.all_single_data_available()
        data_usable = all([col in avail_columns for col in req_columns])
        if not (meta_usable and data_usable):
            logging.warning("CPT with id {} misses required data.".format(data.id))

    @staticmethod
    def parse_xml_location(tdata: bytes):
        """Return x y of location.
        TODO Don't user iter
        :param tdata: XML bytes
        :returns: list -- of x y string coordinates

        Will transform coordinates not in EPSG:28992
        """
        root = etree.fromstring(tdata)
        crs = None

        for loc in root.iter(ns2 + "deliveredLocation"):
            for point in loc.iter(ns3 + "Point"):
                srs = point.get("srsName")
                if srs is not None and "EPSG" in srs:
                    crs = srs.split("::")[-1]
                break
            for pos in loc.iter(ns3 + "pos"):
                x, y = map(float, pos.text.split(" "))
                break

        if crs is not None and crs != to_epsg:
            logging.warning("Reprojecting from epsg::{}".format(crs))
            transformer = pyproj.Transformer.from_crs(f"epsg:{crs}", f"epsg:{to_epsg}")
            x, y = transformer.transform(x, y)

        return x, y

    def get_all_data_from_bro(self, root: _Element) -> None:
        """ Extract values from bro. From the xml elements."""
        # BRO Id
        self.bro_data.id = self.search_values_in_root(
            root=root, search_item=ns4 + "broId"
        )
        # Norm of the cpt
        self.bro_data.cpt_standard = self.search_values_in_root(
            root=root, search_item=ns2 + "cptStandard"
        )
        # Offset to reference point
        z = self.search_values_in_root(root=root, search_item=ns + "offset")
        self.bro_data.offset_z = float(z)
        # Local reference point
        self.bro_data.local_reference = self.search_values_in_root(
            root=root, search_item=ns + "localVerticalReferencePoint"
        )
        # Vertical datum
        self.bro_data.vertical_datum = self.search_values_in_root(
            root=root, search_item=ns + "verticalDatum"
        )
        # cpt class
        self.bro_data.quality_class = self.search_values_in_root(
            root=root, search_item=ns + "qualityClass"
        )
        # cpt type and serial number
        self.bro_data.cone_penetrometer_type = self.search_values_in_root(
            root=root, search_item=ns + "conePenetrometerType"
        )
        # cpt time of result
        for cpt in root.iter(ns + "conePenetrationTest"):
            for loc in cpt.iter(ns5 + "resultTime"):
                self.bro_data.result_time = loc.text
        # Pre drilled depth
        z = self.search_values_in_root(root=root, search_item=ns + "predrilledDepth")
        # if predrill does not exist it is zero
        if not z:
            z = 0.0
        self.bro_data.predrilled_z = float(z)

        # Cone coefficient - a
        a = self.search_values_in_root(
            root=root, search_item=ns + "coneSurfaceQuotient"
        )
        if a:
            self.bro_data.a = float(a)
        return None

    def read_file(self, filepath: Path) -> dict:
        # validate bro xml file
        validate_bro_cpt(filepath)

        # read the BRO_XML into Memory
        xml = self.xml_to_byte_string(filepath)

        # parse the BRO_XML to BRO CPT Dataset
        self.parse_bro_xml(xml)

        # add the BRO_XML attributes to CPT structure
        result_dictionary = self.__parse_bro_raw_data()

        # validate bro xml data
        self.validate_length_and_samples_cpt()

        return result_dictionary

    def __parse_bro_raw_data(self) -> Dict:
        result_dictionary = {
            "name": self.bro_data.id,
            "coordinates": [
                self.bro_data.location_x,
                self.bro_data.location_y,
            ],
            "vertical_datum": self.bro_data.vertical_datum,
            "local_reference": self.bro_data.local_reference,
            "quality_class": self.bro_data.quality_class,
            "cpt_type": self.bro_data.cone_penetrometer_type,
            "cpt_standard": self.bro_data.cpt_standard,
            "result_time": self.bro_data.result_time,
            "local_reference_level": self.bro_data.offset_z,
            "a": [self.bro_data.a],
            "predrilled_z": self.bro_data.predrilled_z,
        }
        result_dictionary["water_measurement_type"] = [
            water_measurement_type
            for water_measurement_type in self.__water_measurement_types
            if water_measurement_type in self.bro_data.dataframe
        ]

        # extract values from dataframe
        if self.bro_data.dataframe is not None:
            bro_dataframe = self.bro_data.dataframe
            for key, value in self.bro_dataframe_map.items():
                result_dictionary[key] = bro_dataframe.get(value, None)
        return self.transform_dict_fields_to_arrays(dictionary=result_dictionary)

    @staticmethod
    def transform_dict_fields_to_arrays(dictionary: Dict) -> Dict:
        for key, value in dictionary.items():
            if isinstance(value, pd.Series):
                dictionary[key] = value.values
        return dictionary

    def check_file_contains_data(self):
        if len(self.bro_data.dataframe.penetrationLength) == 0:
            logging.warning("File " + self.bro_data.id + " contains no data")

    def check_data_different_than_zero(self):
        keys = ["penetrationLength", "coneResistance", "localFriction", "frictionRatio"]
        for k in keys:
            if all(self.bro_data.dataframe[k] == 0):
                logging.warning("File " + self.bro_data.id + " contains empty data")

    def check_criteria_minimum_length(self, minimum_length: int):
        if (
            np.max(np.abs(self.bro_data.dataframe.penetrationLength.values))
            < minimum_length
        ):
            logging.warning(
                "File "
                + self.bro_data.id
                + " has a length smaller than "
                + str(minimum_length)
            )

    def check_minimum_sample_criteria(self, minimum_samples: int):
        if len(self.bro_data.dataframe.penetrationLength.values) < minimum_samples:
            logging.warning(
                "File "
                + self.bro_data.id
                + " has a number of samples smaller than "
                + str(minimum_samples)
            )

    def validate_length_and_samples_cpt(
        self, minimum_length: int = 5, minimum_samples: int = 50
    ):
        """
        Performs initial checks regarding the availability of
        data in the cpt. Returns a string that contains all the
        error messages.
        """

        self.check_file_contains_data()
        self.check_data_different_than_zero()
        self.check_criteria_minimum_length(minimum_length)
        self.check_minimum_sample_criteria(minimum_samples)
