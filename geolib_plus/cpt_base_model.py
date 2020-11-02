from abc import abstractmethod
from pathlib import Path
from typing import Optional, Iterable, List
from pydantic import BaseModel
from copy import deepcopy
import numpy as np

from .plot_cpt import plot_cpt_norm
from .plot_settings import PlotSettings


class AbstractInterpretationMethod:
    """Base Interpretation method for analyzing CPTs."""


class RobertsonMethod(AbstractInterpretationMethod):
    """Scientific explanation about this method."""


class CptReader:
    @abstractmethod
    def read_file(self, filepath: Path) -> dict:
        raise NotImplementedError(
            "The method should be implemented in concrete classes."
        )


class AbstractCPT(BaseModel):
    """Base CPT class, should define abstract."""

    #  variables
    penetration_length: Optional[Iterable]
    depth: Optional[Iterable]
    coordinates: Optional[List]
    local_reference_level: Optional[float]
    depth_to_reference: Optional[Iterable]
    tip: Optional[Iterable]
    friction: Optional[Iterable]
    friction_nbr: Optional[Iterable]
    a: Optional[Iterable]
    name: Optional[str]
    rho: Optional[Iterable]
    total_stress: Optional[Iterable]
    effective_stress: Optional[Iterable]
    pwp: Optional[Iterable]
    qt: Optional[Iterable]
    Qtn: Optional[Iterable]
    Fr: Optional[Iterable]
    IC: Optional[Iterable]
    n: Optional[Iterable]
    vs: Optional[Iterable]
    G0: Optional[Iterable]
    E0: Optional[Iterable]
    permeability: Optional[Iterable]
    poisson: Optional[Iterable]
    damping: Optional[Iterable]

    pore_pressure_u1: Optional[Iterable]
    pore_pressure_u2: Optional[Iterable]
    pore_pressure_u3: Optional[Iterable]

    water: Optional[Iterable]
    lithology = []
    litho_points = []

    lithology_merged = []
    depth_merged = []
    index_merged = []
    vertical_datum: Optional[str]
    local_reference: Optional[str]
    inclination_x: Optional[Iterable]
    inclination_y: Optional[Iterable]
    inclination_ns: Optional[Iterable]
    inclination_ew: Optional[Iterable]
    inclination_resultant: Optional[Iterable]
    time: Optional[Iterable]
    net_tip: Optional[Iterable]
    pore_ratio: Optional[Iterable]
    tip_nbr = []
    unit_weight_measured: Optional[Iterable]
    pwp_ini: Optional[Iterable]
    total_pressure_measured: Optional[Iterable]
    effective_pressure_measured: Optional[Iterable]
    electric_cond: Optional[Iterable]
    magnetic_strength_x: Optional[Iterable]
    magnetic_strength_y: Optional[Iterable]
    magnetic_strength_z: Optional[Iterable]
    magnetic_strength_tot: Optional[Iterable]
    magnetic_inclination: Optional[Iterable]
    magnetic_declination: Optional[Iterable]

    cpt_standard: Optional[str]
    quality_class: Optional[str]
    cpt_type: Optional[str]
    result_time: Optional[str]
    water_measurement_type: Optional[str]

    # NEN results
    litho_NEN = []
    E_NEN = []
    cohesion_NEN = []
    fr_angle_NEN = []

    # fixed values
    g: float = 9.81
    Pa: float = 100.0

    # private variables
    __water_measurement_types = None

    @classmethod
    def read(cls, filepath: Path):
        if not filepath:
            raise ValueError(filepath)

        filepath = Path(filepath)
        if not filepath.is_file():
            raise FileNotFoundError(filepath)

        cpt_reader = cls.get_cpt_reader()
        cpt_data = cpt_reader.read_file(filepath)
        cpt_model = cls()
        for cpt_key, cpt_value in cpt_data.items():
            setattr(cpt_model, cpt_key, cpt_value)
        return cpt_model

    @classmethod
    @abstractmethod
    def get_cpt_reader(cls) -> CptReader:
        raise NotImplementedError("Should be implemented in concrete class.")


    def __calculate_corrected_depth(self) -> np.ndarray:
        """
        Correct the penetration length with the inclination angle


        :param penetration_length: measured penetration length
        :param inclination: measured inclination of the cone
        :return: corrected depth
        """
        corrected_d_depth = np.diff(self.penetration_length) * np.cos(
            np.radians(self.inclination_resultant[:-1])
        )
        corrected_depth = np.concatenate(
            (
                self.penetration_length[0],
                self.penetration_length[0] + np.cumsum(corrected_d_depth),
            ),
            axis=None,
        )
        return corrected_depth

    def calculate_depth(self):
        """
        If depth is present in the bro cpt and is valid, the depth is parsed from depth
        elseif resultant inclination angle is present and valid in the bro cpt, the penetration length is corrected with
        the inclination angle.
        if both depth and inclination angle are not present/valid, the depth is parsed from the penetration length.
        :param cpt_BRO: dataframe
        :return:
        """

        if self.depth.size == 0:
            if self.inclination_resultant.size != 0:
                self.depth = self.__calculate_corrected_depth()
            else:
                self.depth = deepcopy(self.penetration_length)

    @staticmethod
    def __correct_for_negatives(data):
        """
        Values tip / friction / friction cannot be negative so they
        have to be zero.
        """
        if data is not None:
            if data.size != 0 and not data.ndim:
                data[data<0] = 0
            return data

    def __get_water_data(self):

        pore_pressure_data = [self.pore_pressure_u1, self.pore_pressure_u2, self.pore_pressure_u3]

        for data in pore_pressure_data:
            if data is not None:
                if data.size and data.ndim:
                    self.water = deepcopy(data)
                    break
        if self.water is None:
            self.water = np.zeros(len(self.penetration_length))

    def pre_process_data(self):
        self.calculate_depth()
        self.depth_to_reference = self.local_reference_level - self.depth

        # correct tip friction and friction number for negative values
        self.tip = self.__correct_for_negatives(self.tip)
        self.friction = self.__correct_for_negatives(self.friction)
        self.friction_nbr = self.__correct_for_negatives(self.friction_nbr)

        self.__get_water_data()
        pass


    def plot(self, directory: Path):
        # plot cpt data
        try:
            plot_setting = PlotSettings()
            plot_setting.assign_default_settings()
            plot_cpt_norm(self, directory, plot_setting.general_settings)

        except (ValueError, IndexError):
            print("Cpt data and/or settings are not valid")
        except PermissionError as error:
            print(error)
