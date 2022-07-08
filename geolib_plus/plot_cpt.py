from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from geolib_plus.cpt_base_model import AbstractCPT

import os
import warnings
from pathlib import Path
from typing import Tuple

import matplotlib.pylab as plt
import numpy as np

from geolib_plus import plot_utils


def get_values_which_exceed_threshold(
    threshold: List, values: np.ndarray, y_data: np.ndarray, show_interval: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gets the values which exceed the given threshold which has to be shown, where a value is shown if the distance
    regarding the previous shown value is greater than the show interval and the value exceeds the threshold.

    :param threshold:               Threshold values of plotted data
    :param values:                  Plotted data
    :param y_data:                  Depth data
    :param show_interval:           Min distance between shown values
    :return shown_values:           Values past threshold which are shown in text boxes
    :return y_coord_shown_value:    Vertical coordinates of the shown_values
    """

    shown_values = []
    y_coord_shown_value = []

    for idx, value in enumerate(values):
        if value > threshold[1] and idx < len(values) - 1:
            if not y_coord_shown_value:
                shown_values.append(value)
                y_coord_shown_value.append(y_data[idx])
            elif y_data[idx] <= y_coord_shown_value[-1] - show_interval:
                shown_values.append(value)
                y_coord_shown_value.append(y_data[idx])

    return np.array(shown_values), np.array(y_coord_shown_value)


def trim_values_at_exceeding_threshold(threshold: List, values: np.ndarray) -> np.ndarray:
    """
    Trims a graph on threshold values when the threshold is exceeded.

    :param threshold:
    :param values:
    :return trimmed values:
    """

    return np.clip(values, threshold[0], threshold[1])


def get_y_lims(cpt: AbstractCPT, settings: Dict) -> List:
    """
    Gets all the vertical plot limits of the cpt. If the length of the cpt exceeds the vertical limit of the plot, a new
    plot is generated. The top of the new plot is the bottom of the previous plot plus the repeated distance

    :param cpt:
    :param settings:
    :return:
    """

    vertical_settings = settings["vertical_settings"]

    if vertical_settings["top_type"] == "relative":
        y_max = np.ceil(cpt.local_reference_level) + vertical_settings["buffer_at_top"]
    elif vertical_settings["top_type"] == "absolute":
        y_max = vertical_settings["absolute_top_level"]
    else:
        Warning("top type is not recognized in vertical settings")
        raise ValueError

    y_min = np.floor(np.min(cpt.depth_to_reference))

    if vertical_settings["repeated_distance"] > vertical_settings["length_graph"]:
        Warning("repeated distance cannot be greater than length graph")
        raise ValueError

    n_graphs = int(np.ceil((y_max - y_min) / vertical_settings["length_graph"]))
    n_graphs = int(
        np.ceil(
            (n_graphs * vertical_settings["repeated_distance"] + np.ceil((y_max - y_min)))
            / vertical_settings["length_graph"]
        )
    )

    if settings["plot_size"] == "a4":
        y_lims = [
            [
                y_max
                - n_graph
                * (
                    vertical_settings["length_graph"]
                    - vertical_settings["repeated_distance"]
                ),
                y_max
                - vertical_settings["length_graph"]
                - n_graph
                * (
                    vertical_settings["length_graph"]
                    - vertical_settings["repeated_distance"]
                ),
            ]
            for n_graph in range(n_graphs)
        ]
    elif settings["plot_size"] == "unlimited":
        y_lims = [[y_max, min(y_min, y_max - vertical_settings["length_graph"])]]
    else:
        Warning("settings: " + settings["plot_size"] + "is not recognized")
        raise ValueError

    return y_lims


def trim_cpt_data_on_vertical_limits(
    cpt: AbstractCPT, y_lim: List, settings: Dict
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Trims the cpt data on the vertical limits.

    :param cpt: cpt data
    :param y_lim: vertical limit of current graph
    :param settings: graph settings
    :return:
    """

    # Get the data
    data = []
    if settings["data_key"] == "qc":
        data = cpt.tip
    if settings["data_key"] == "friction":
        data = cpt.friction
    if settings["data_key"] == "friction_nbr":
        data = cpt.friction_nbr
    if settings["data_key"] == "inv_friction_nbr":
        data = cpt.tip / cpt.friction
    if settings["data_key"] == "water":
        data = cpt.water

    # Prevent plotting estimated predrill and invalid data
    valid_depth = cpt.depth_to_reference[
        cpt.depth_to_reference <= cpt.local_reference_level - cpt.undefined_depth
    ]
    valid_data = data[
        cpt.depth_to_reference <= cpt.local_reference_level - cpt.undefined_depth
    ]

    # Get the data which falls within the vertical limits of the plot
    depth_in_range_idxs = np.where((y_lim[1] < valid_depth) & (valid_depth < y_lim[0]))
    data_within_lim = valid_data[depth_in_range_idxs].tolist()
    depth_in_range = valid_depth[depth_in_range_idxs].tolist()
    if isinstance(cpt.inclination_resultant, np.ndarray):
        valid_inclination = cpt.inclination_resultant[
            cpt.depth_to_reference <= cpt.local_reference_level - cpt.undefined_depth
        ]
        inclination_in_range = valid_inclination[depth_in_range_idxs].tolist()
    else:
        inclination_in_range = None

    # If multiple plots are required to show the data, add last value of previous plot to current plot
    if cpt.depth_to_reference[0] > y_lim[0]:
        previous_idx = max(
            i for i in range(len(valid_depth)) if valid_depth[i] - y_lim[0] > 0
        )
        data_within_lim.insert(0, valid_data[previous_idx])
        depth_in_range.insert(0, valid_depth[previous_idx])
        if inclination_in_range is not None:
            inclination_in_range.insert(0, valid_inclination[previous_idx])

    data_within_lim = np.array(data_within_lim)
    depth_in_range = np.array(depth_in_range)
    inclination_in_range = np.array(inclination_in_range)

    return depth_in_range, inclination_in_range, data_within_lim


def trim_cpt_data(
    settings: Dict, vertical_settings: Dict, cpt: AbstractCPT, y_lim: List
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Trims the requested cpt data (qc ,friction, friction nbr, water) at threshold values and vertical limits.

    :param settings:                graph settings
    :param vertical_settings:       the vertical settings
    :param cpt:                     cpt data
    :param y_lim:                   vertical limit of current graph
    :return trimmed_values:         Trimmed cpt data at cut off values
    :return shown_values:           Values past threshold which are shown in text boxes
    :return y_coord_shown_value:    Vertical coordinates of the shown_values
    :return depth_in_range:         Vertical coordinates within y limits
    :return inclination_in_range:   Inclination angle within y limits
    """

    # trim data on vertical limits
    (
        depth_in_range,
        inclination_in_range,
        data_within_lim,
    ) = trim_cpt_data_on_vertical_limits(cpt, y_lim, settings)

    # trim data on threshold values
    threshold = [
        settings["threshold"][0] * settings["unit_converter"],
        settings["threshold"][1] * settings["unit_converter"],
    ]

    trimmed_values = trim_values_at_exceeding_threshold(
        threshold, data_within_lim * settings["unit_converter"]
    )

    # get values past exceeding thresholds which has to be shown in graph
    shown_values, y_coord_shown_value = get_values_which_exceed_threshold(
        threshold,
        data_within_lim * settings["unit_converter"],
        depth_in_range,
        vertical_settings["spacing_shown_cut_off_value"],
    )

    return (
        trimmed_values,
        shown_values,
        y_coord_shown_value,
        depth_in_range,
        inclination_in_range,
    )


def define_inclination_ticks_and_labels(
    cpt: AbstractCPT,
    depth: np.ndarray,
    inclination: np.ndarray,
    ylim: List,
    settings: Dict,
) -> Tuple[np.ndarray, List]:
    """
    Defines the location and the labels of the ticks referring to the inclination angle with respect to the depth of the
    cpt. The first tick is at the reference level, the following ticks are spaced exactly 1 meter apart. The tick label
    is defined as the average inclination over the 1 meter above the tick.

    :param cpt:
    :param depth:
    :param inclination:
    :param ylim:
    :param settings:
    :return:
    """
    if all(inclination == np.array([None])):
        return np.array([]), []

    tick_distance_from_ceil_meter = cpt.local_reference_level - np.ceil(
        cpt.local_reference_level
    )
    tick_distance_inclination = settings["vertical_settings"]["inclination_tick_distance"]

    if cpt.local_reference_level < ylim[0]:
        tick_locations_inclination = np.arange(
            cpt.local_reference_level,
            ylim[1] + tick_distance_from_ceil_meter,
            -tick_distance_inclination,
        )
    else:
        tick_locations_inclination = np.arange(
            ylim[0] + tick_distance_from_ceil_meter,
            ylim[1] + tick_distance_from_ceil_meter,
            -tick_distance_inclination,
        )
    if tick_locations_inclination.size == 0:
        return np.array([]), []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        tick_labels_inclination = np.array(
            [
                np.nanmean(
                    inclination[
                        (depth > tick_locations_inclination[idx + 1])
                        & (depth < tick_locations_inclination[idx])
                    ].tolist()
                )
                for idx in range(0, len(tick_locations_inclination) - 1)
            ]
        )

    tick_labels_inclination = np.insert(tick_labels_inclination, 0, inclination[0])

    number_idxs = np.where(~np.isnan(tick_labels_inclination))
    tick_locations_inclination = tick_locations_inclination[number_idxs]
    tick_labels_inclination = [
        "{0:.1f}".format(tick_label)
        for tick_label in tick_labels_inclination[number_idxs]
    ]

    return tick_locations_inclination, tick_labels_inclination


def save_figures(figures: List, cpt: AbstractCPT, output_folder: Path):
    """
    Saves all plots of current cpt in one pdf file

    :param fig: current figure
    :param ylims: all vertical limits of current cpt
    :param cpt: cpt data
    :param plot_nr: number of the plot
    :return:
    """

    import matplotlib.backends.backend_pdf

    if not output_folder.exists():
        output_folder.mkdir(parents=True)

    pdf = matplotlib.backends.backend_pdf.PdfPages(
        Path(output_folder / (cpt.name + ".pdf"))
    )

    for fig in figures:
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    pdf.close()


def generate_plot(
    cpt: AbstractCPT, settings: Dict, ylim: List, ylims: List, plot_nr: int
) -> plt.Figure:
    """
    Plots cpt data within vertical limits

    :param cpt: cpt data
    :param settings: general settings
    :param ylim: current vertical limit
    :param ylims: all vertical limits for the current cpt data
    :param plot_nr: number of the plot within the current cpt data
    :return:
    """
    fig = plt.figure()
    axes = [fig.add_subplot(111)]

    for idx, (key, graph) in enumerate(settings["graph_settings"].items()):
        trimmed_data, max_data, found_depths_data, depths, inclination = trim_cpt_data(
            graph, settings["vertical_settings"], cpt, ylim
        )
        do_create_axis = np.count_nonzero(trimmed_data) > 0

        if do_create_axis:
            ax = axes[0].twiny() if idx > 0 else axes[0]

            # plot data
            ax.plot(
                trimmed_data,
                depths,
                color=graph["graph_color"],
                linestyle=graph["line_style"],
            )

            # set x axis
            ax = plot_utils.set_x_axis(
                ax,
                graph,
                settings,
                ylim,
            )

            # set text boxes at values which exceed the threshold

            plot_utils.set_textbox_at_thresholds(
                ax,
                ylim,
                max_data,
                found_depths_data,
                graph["threshold"] * graph["unit_converter"],
                graph["position_label"],
            )

            axes.append(ax)

    axes[
        0
    ].xaxis.tick_top()  # todo improve this, as this assumes a fixed order of the added data

    # set the y axis
    (
        tick_locations_inclination,
        tick_labels_inclination,
    ) = define_inclination_ticks_and_labels(cpt, depths, inclination, ylim, settings)
    plot_utils.set_y_axis(
        axes[0],
        ylim,
        settings,
        cpt,
        tick_locations_inclination,
        tick_labels_inclination,
    )

    # set surface line
    plot_utils.set_local_reference_line(
        cpt, axes[0], axes[0].get_xlim(), settings["language"]
    )

    # create custom grid
    plot_utils.create_custom_grid(axes[0], axes[0].get_xlim(), ylim, settings["grid"])

    # set size in inches
    plot_utils.set_figure_size(fig, ylim)

    scale = 0.8

    fig.subplots_adjust(top=scale, left=1 - scale)

    # add information_box
    plot_utils.create_information_box(
        axes[0], scale, cpt, plot_nr, ylims, settings["distance_from_plot"]
    )

    return fig


def plot_cpt_norm(cpt: AbstractCPT, output_folder: Path, settings: Dict):
    """
    Plots and saves all data in the current cpt according to the norm written in NEN 22476-1

    :param cpt: cpt data
    :param settings: general settings
    :return:
    """

    # validate that plotting can be run
    cpt.has_points_with_error()
    cpt.are_data_available_plotting()
    cpt.has_duplicated_depth_values()
    cpt.check_if_lists_have_the_same_size()

    # Get vertical limits of the plotted data
    ylims = get_y_lims(cpt, settings)

    # loop over all vertical limits within the current cpt data
    figures = []
    for plot_nr, ylim in enumerate(ylims):
        figures.append(generate_plot(cpt, settings, ylim, ylims, plot_nr))

    save_figures(figures, cpt, output_folder)

    plt.close("all")
