from typing import Dict, Optional

import numpy as np


class PlotSettings:
    def __init__(self):
        self.plot_qc_settings: Optional[Dict] = {}  # Settings for cone resistance graph
        self.plot_friction_settings: Optional[
            Dict
        ] = {}  # Settings for friction resistance graph
        self.plot_friction_nbr_settings: Optional[
            Dict
        ] = {}  # Settings for friction number graph
        self.plot_inv_friction_nbr_settings: Optional[
            Dict
        ] = {}  # Settings for inversed friction number graph
        self.plot_water_settings: Optional[Dict] = {}  # Settings for pore pressure graph
        self.general_settings: Optional[Dict] = {}  # All settings
        self.grid: Optional[Dict] = {}  # Settings for grid in plot
        self.vertical_settings: Optional[
            Dict
        ] = {}  # Settings for the vertical axis in the graph

        # private variables are assigned for settings which can be altered with a limit set of options
        self.__languages = ["Nederlands", "English"]
        self.__data_keys = [
            "qc",
            "friction",
            "friction_nbr",
            "water",
            "inv_friction_nbr",
        ]
        self.__unit_converters = {
            "None": 1,
            "kPa_To_Pa": 1e3,
            "MPa_To_kPa": 1e3,
            "MPa_To_Pa": 1e6,
            "Pa_To_kPa": 1 / 1e3,
            "kPa_To_MPa": 1 / 1e3,
            "Pa_To_MPa": 1 / 1e6,
        }
        self.__line_styles = ["-", "--", "-.", ":"]
        self.__label_positions = [
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
            "bottom_middle",
            "top_middle",
        ]
        self.__plot_sizes = ["a4", "unlimited"]
        self.__top_types = ["relative", "absolute"]
        self.__x_axis_type = ["primary", "secondary"]

        self.assign_default_settings()

    @property
    def languages(self):
        """
        Language of the plot, options are:
            0 = 'Nederlands',
            1 = 'English'
        """
        return self.__languages

    @property
    def data_keys(self):
        return self.__data_keys

    @property
    def unit_converters(self):
        return self.__unit_converters

    @property
    def line_styles(self):
        return self.__line_styles

    @property
    def label_positions(self):
        """
        Position of the label in the plot, options are:
            0 = 'top_left',
            1 = 'top_right',
            2 = 'bottom_left',
            3 = 'bottom_right',
            4 = 'bottom_middle',
        """
        return self.__label_positions

    @property
    def plot_sizes(self):
        """
        Size of the plot, options are:
            0 = 'a4';
            1 = 'unlimited';
        """
        return self.__plot_sizes

    @property
    def top_types(self):
        """
        Type of the top level of the plot, options are:
            0 = 'relative' : the top of the plot is relative to the surface level;
            1 = 'absolute' : the top of the plot is an absolute value;
        """
        return self.__top_types

    def assign_default_settings(self):
        """
        Assigns the default plot settings
        :return:
        """

        self.plot_qc_settings = {
            "data_key": self.__data_keys[0],
            "threshold": [0, 28],
            "graph_color": "red",
            "line_style": self.__line_styles[0],
            "label": {
                self.__languages[0]: "Conusweerstand [MPa]",
                self.__languages[1]: "Tip resistance [MPa]",
            },
            "position_label": self.__label_positions[0],
            "scale_unit": 2,
            "shift_graph": 0,
            "unit_converter": self.__unit_converters["None"],
            "ticks": np.arange(0, 30, 10).tolist(),
            "x_axis_type": self.__x_axis_type[0],
        }

        self.plot_friction_settings = {
            "data_key": self.__data_keys[1],
            "threshold": [0, 0.7],
            "graph_color": "blue",
            "line_style": self.__line_styles[1],
            "label": {
                self.__languages[0]: "Wrijvingsweerstand [MPa]",
                self.__languages[1]: "Friction resistance [MPa]",
            },
            "position_label": self.__label_positions[2],
            "scale_unit": 0.050,
            "shift_graph": 0,
            "unit_converter": self.__unit_converters["None"],
            "ticks": np.arange(0, 0.3, 0.1).tolist(),
            "x_axis_type": self.__x_axis_type[0],
        }

        self.plot_friction_nbr_settings = {
            "data_key": self.__data_keys[2],
            "threshold": [0, 18],
            "graph_color": "green",
            "line_style": self.__line_styles[2],
            "label": {
                self.__languages[0]: "Wrijvingsgetal [%]",
                self.__languages[1]: "Friction number [%]",
            },
            "position_label": self.__label_positions[3],
            "scale_unit": 2,
            "shift_graph": 0,
            "unit_converter": self.__unit_converters["None"],
            "ticks": np.arange(0, 12, 2).tolist(),
            "x_axis_type": self.__x_axis_type[0],
        }

        self.plot_inv_friction_nbr_settings = {
            "data_key": self.__data_keys[4],
            "threshold": [0, 900],
            "graph_color": "green",
            "line_style": self.__line_styles[2],
            "label": {
                self.__languages[0]: "qc / fs [-]",
                self.__languages[1]: "qc / fs [-]",
            },
            "position_label": self.__label_positions[3],
            "scale_unit": 100,
            "shift_graph": 0,
            "unit_converter": self.__unit_converters["None"],
            "ticks": np.arange(0, 600, 100).tolist(),
            "x_axis_type": self.__x_axis_type[0],
        }

        self.plot_water_settings = {
            "data_key": self.__data_keys[3],
            "threshold": [-0.200, 1],
            "graph_color": "saddlebrown",
            "line_style": self.__line_styles[3],
            "label": {
                self.__languages[0]: "Waterdruk [MPa]",
                self.__languages[1]: "Water pressure [MPa]",
            },
            "position_label": self.__label_positions[4],
            "scale_unit": 0.200,
            "shift_graph": 1,
            "unit_converter": self.__unit_converters["None"],
            "ticks": np.arange(0, 1.0, 0.2).tolist(),
            "x_axis_type": self.__x_axis_type[0],
        }

        graph_settings = {
            self.__data_keys[0]: self.plot_qc_settings,
            self.__data_keys[1]: self.plot_friction_settings,
            self.__data_keys[2]: self.plot_friction_nbr_settings,
            self.__data_keys[3]: self.plot_water_settings,
        }

        self.grid = {
            "reference_data_key": self.__data_keys[0],
            "vertical_major_line_locations": [10, 20],
            "vertical_major_line_color": "gray",
            "vertical_major_line_line_width": 1.2,
            "vertical_minor_line_distances": [2, 1],
            "vertical_minor_line_colors": ["gray", "gray"],
            "vertical_minor_line_line_widths": [0.5, 0.25],
            "horizontal_major_line_locations": [],
            "horizontal_major_line_color": "gray",
            "horizontal_major_line_line_width": 1.2,
            "horizontal_line_distances": [1, 0.5],
            "horizontal_line_colors": ["gray", "gray"],
            "horizontal_line_line_widths": [0.5, 0.25],
        }

        self.vertical_settings = {
            "top_type": self.__top_types[0],
            "absolute_top_level": 0,  # [m]
            "buffer_at_top": 1,  # [m]
            "length_graph": 21,  # [m]
            "repeated_distance": 1,  # [m]
            "depth_tick_distance": 1,  # [m]
            "inclination_tick_distance": 1,  # [m]
            "spacing_shown_cut_off_value": 1,  # [m]
            "y_label_depth": {
                "Nederlands": "Diepte in meters ten opzichte van ",
                "English": "Depth in meter relative to ",
            },
            "y_label_inclination": {
                "Nederlands": "Resultante hellingshoek $\\alpha$ [$\\degree$]",
                "English": "Resultant inclination angle $\\alpha$ [$\\degree$]",
            },
        }

        self.general_settings = {
            "graph_settings": graph_settings,
            "grid": self.grid,
            "language": self.__languages[0],
            "vertical_settings": self.vertical_settings,
            "nbr_scale_units": 16,
            "font_size_labels": 8,
            "plot_size": self.__plot_sizes[0],
            "distance_from_plot": -1,
        }

    def set_inversed_friction_number_in_plot(self):
        """
        Removes friction number from the plot and sets the inverse friction number in the plot
        :return:
        """
        self.general_settings["graph_settings"].pop(self.__data_keys[2], None)
        self.general_settings["graph_settings"][
            self.__data_keys[-1]
        ] = self.plot_inv_friction_nbr_settings

    def set_friction_number_in_plot(self):
        """
        Removes inverse friction number from the plot and sets the friction number in the plot
        :return:
        """
        self.general_settings["graph_settings"].pop(self.__data_keys[-1], None)
        self.general_settings["graph_settings"][
            self.__data_keys[2]
        ] = self.plot_friction_nbr_settings
