from typing import List

import numpy as np
from matplotlib.axes import Axes
from matplotlib.offsetbox import AnchoredOffsetbox, HPacker, TextArea
from matplotlib.patches import Rectangle

CALIBRATED_LENGTH_FIGURE_SIZE = (
    21  # layout figure is calibrated using a plotted depth of 21 m
)
A4_WIDTH = 8.27  # inches
A4_LENGTH = 11.69  # inches


def set_textbox_at_thresholds(
    ax: Axes,
    ylim: List,
    max_data: np.ndarray,
    found_depths_data: np.ndarray,
    threshold: List,
    location: str,
):
    """
    Set textboxes in the plot at the location off maximum values past the cut off value.

    :param ax:                  axis
    :param ylim:                vertical limit
    :param max_data:            maximum values past the cut off value
    :param found_depths_data:   depths of maximum values past the cut of value
    :param threshold:           value at which the data is cut off
    :param location:            location of axis label and ticks
    :return:
    """

    # get relative position of the cut off value on the plot
    xlim = ax.get_xlim()
    cut_off_position = (threshold[1] - xlim[0]) / (xlim[1] - xlim[0])

    # set x-position of the textbox near the cut off position
    if location == "top_left" or location == "bottom_left" or location == "bottom_middle":
        label_x_position = cut_off_position + 0.08
        loc = 4
    else:
        label_x_position = cut_off_position - 0.08
        loc = 3

    vertical_spacing = 0.1 * CALIBRATED_LENGTH_FIGURE_SIZE / (ylim[0] - ylim[1])

    # Get relative vertical positions of the textboxes in the plot. And sets the horizontal en vertical positions.
    positions = [
        (
            label_x_position,
            (ylim[1] - found_depth + vertical_spacing) / (ylim[1] - ylim[0]),
        )
        for found_depth in found_depths_data
    ]

    for idx, position in enumerate(positions):

        # generate label text
        if (
            location == "top_left"
            or location == "bottom_left"
            or location == "bottom_middle"
        ):
            label_text = r"$\longleftarrow$" + "{0:.2f}".format(max_data[idx])
        else:
            label_text = str(max_data[idx]) + r"$\longrightarrow$"

        # generate text box
        boxes = [
            TextArea(
                label_text,
                textprops=dict(color="black", fontsize=6, horizontalalignment="left"),
            )
        ]
        xbox = HPacker(children=boxes, align="center", pad=0, sep=5)
        anchored_xbox = AnchoredOffsetbox(
            loc=loc,
            child=xbox,
            pad=0,
            frameon=False,
            bbox_to_anchor=position,
            bbox_transform=ax.transAxes,
            borderpad=0.0,
        )

        # set text box in plot
        ax.add_artist(anchored_xbox)


def set_multicolor_label(
    ylim,
    ax,
    label_txt,
    color,
    font_size_text,
    font_size_arrow,
    line_style,
    x_axis_type,
    location="bottom_left",
    axis="x",
    anchorpad=0,
    **kw,
):
    """
    This function creates axes labels with multiple colors

    :param ylim: vertical limit of current plot
    :param ax: current axis where the labels should be drawn
    :param label_txt: text in label
    :param color: color of label
    :param font_size_text: font size of the text
    :param font_size_arrow: font size of the arrow in the label
    :param line_style: style of the line of the current graph
    :param location: location of the label relative to the plot
    :param axis: 'x', 'y', or 'both' and specifies which label(s) should be drawn
    :param anchorpad: pad around the child for drawing a frame. given in fraction of fontsize.
    :param kw: key word arguments for TextArea
    :return:
    """

    if line_style == "--":
        line_style_string = r"\dash"
    else:
        line_style_string = "\\"

    is_inverted = False
    vertical_rel_spacing = 0.06 * CALIBRATED_LENGTH_FIGURE_SIZE / (ylim[0] - ylim[1])
    if not (x_axis_type == "primary"):
        vertical_rel_spacing += 0.01
    axis_plot = ax.xaxis
    if location == "top_left":
        bbox_to_anchor = (0.0, 1 + vertical_rel_spacing)
        loc = 2
        axis_plot.tick_top()
    elif location == "top_right":
        bbox_to_anchor = (1.0, 1 + vertical_rel_spacing)
        loc = 1
        axis_plot.tick_top()
        is_inverted = True
    elif location == "top_middle":
        bbox_to_anchor = (5 / 16, 1 + vertical_rel_spacing)
        loc = 2
        axis_plot.tick_top()
    elif location == "bottom_left":
        bbox_to_anchor = (0.0, -vertical_rel_spacing)
        loc = 3
        axis_plot.tick_bottom()
    elif location == "bottom_right":
        bbox_to_anchor = (1.0, -vertical_rel_spacing)
        loc = 4
        axis_plot.tick_bottom()
        is_inverted = True
    else:  # bottom_center
        bbox_to_anchor = (5 / 16, -vertical_rel_spacing)
        loc = 3
        axis_plot.tick_bottom()

    if is_inverted:
        arrow_string = r"$" + line_style_string + "leftarrow$"
        list_of_strings = [arrow_string, label_txt]
        list_of_colors = [color, "black"]
        font_size_list = [font_size_arrow, font_size_text]
        ax.invert_xaxis()
    else:
        arrow_string = r"$" + line_style_string + "rightarrow$"
        list_of_strings = [label_txt, arrow_string]
        list_of_colors = ["black", color]
        font_size_list = [font_size_text, font_size_arrow]

    # x-axis label
    if axis == "x" or axis == "both":
        boxes = [
            TextArea(
                text,
                textprops=dict(
                    color=color, fontsize=fontsize, horizontalalignment="left", **kw
                ),
            )
            for text, color, fontsize in zip(
                list_of_strings, list_of_colors, font_size_list
            )
        ]

        xbox = HPacker(children=boxes, align="center", pad=0, sep=5)

        anchored_xbox = AnchoredOffsetbox(
            loc=loc,
            child=xbox,
            pad=anchorpad,
            frameon=False,
            bbox_to_anchor=bbox_to_anchor,
            bbox_transform=ax.transAxes,
            borderpad=0.0,
        )
        ax.add_artist(anchored_xbox)


def set_local_reference_line(cpt, ax, xlim, language):
    """
    Sets a line in the plot at the depth of the  local reference line, e.g. surface level or sea bed level.
    Also set a textbox with the depth of the reference line relative to the vertical datum.

    :param cpt:
    :param ax:
    :param xlim:
    :param language:
    :return:
    """

    bbox_to_anchor = (5 / 16, 1)  # top middle
    loc = 2

    ax.plot(
        xlim,
        [cpt.local_reference_level, cpt.local_reference_level],
        color="black",
        linewidth=2,
    )

    if language == "Nederlands":
        text = (
            cpt.local_reference
            + " = "
            + str(cpt.local_reference_level)
            + "   m t.o.v. "
            + cpt.vertical_datum
        )
    else:
        text = (
            cpt.local_reference
            + " = "
            + str(cpt.local_reference_level)
            + "   m relative to "
            + cpt.vertical_datum
        )

    box = [
        TextArea(
            text, textprops=dict(color="black", fontsize=9, horizontalalignment="left")
        )
    ]

    xbox = HPacker(children=box, align="center", pad=0, sep=5)

    anchored_xbox = AnchoredOffsetbox(
        loc=loc,
        child=xbox,
        pad=0.25,
        frameon=True,
        bbox_to_anchor=bbox_to_anchor,
        bbox_transform=ax.transAxes,
        borderpad=0.0,
    )
    ax.add_artist(anchored_xbox)


def create_custom_grid(ax, xlim, ylim, grid):
    """
    Creates custom grid with custom line colours, custom line distances and custom line widths

    :param ax: current axis
    :param xlim: horizontal limit
    :param ylim: vertical limit
    :param grid: grid settings
    :return:
    """

    # create major vertical grid lines
    grid_lines = np.array(grid["vertical_major_line_locations"])
    [
        ax.plot(
            [x_line, x_line],
            ylim,
            color=grid["vertical_major_line_color"],
            linewidth=grid["vertical_major_line_line_width"],
        )
        for x_line in grid_lines
    ]

    # create minor vertical grid lines
    for idx, x_distance in enumerate(grid["vertical_minor_line_distances"]):
        grid_lines = np.arange(xlim[0], xlim[1], x_distance)
        [
            ax.plot(
                [x_line, x_line],
                ylim,
                color=grid["vertical_minor_line_colors"][idx],
                linewidth=grid["vertical_minor_line_line_widths"][idx],
            )
            for x_line in grid_lines
        ]

    # create major vertical grid lines
    grid_lines = np.array(grid["horizontal_major_line_locations"])
    [
        ax.plot(
            xlim,
            [y_line, y_line],
            color=grid["horizontal_major_line_color"],
            linewidth=grid["horizontal_major_line_line_width"],
        )
        for y_line in grid_lines
    ]

    # create horizontal grid lines
    for idx, y_distance in enumerate(grid["horizontal_line_distances"]):
        grid_lines = np.arange(ylim[1], ylim[0], y_distance)
        [
            ax.plot(
                xlim,
                [y_line, y_line],
                color=grid["horizontal_line_colors"][idx],
                linewidth=grid["horizontal_line_line_widths"][idx],
            )
            for y_line in grid_lines
        ]


def set_x_axis(ax, graph, settings, ylim):
    """
    Sets the x-limit, the x-label, and the x-ticks

    :param ax:
    :param graph:
    :param settings:
    :return:
    """

    x_label = graph["label"][settings["language"]]
    x_lim = [
        (0 - graph["shift_graph"] * graph["unit_converter"]),
        (
            settings["nbr_scale_units"] * graph["scale_unit"] * graph["unit_converter"]
            - graph["shift_graph"] * graph["unit_converter"]
        ),
    ]

    ticks = graph["ticks"]

    if not (graph["x_axis_type"] == "primary"):
        ax.spines["top"].set_position(("axes", 1.034))
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.spines["top"].set_visible(True)
        # ax.spines["top"].set_edgecolor(graph["graph_color"])
    ax.set_xlim(x_lim)
    ax.set_xticks(ticks)
    ax.tick_params(axis="x", colors=graph["graph_color"])

    set_multicolor_label(
        ylim,
        ax,
        x_label,
        graph["graph_color"],
        settings["font_size_labels"],
        settings["font_size_labels"] * 2,
        graph["line_style"],
        graph["x_axis_type"],
        location=graph["position_label"],
    )

    return ax


def set_y_axis(
    ax, ylim, settings, cpt, tick_locations_inclination, tick_labels_inclination
):
    """
    Sets the y-limit, the y-label, the y-ticks and inverts y-axis

    :param ax:
    :param ylim:
    :param settings:
    :param cpt:
    :return:
    """

    y_label_depth = (
        settings["vertical_settings"]["y_label_depth"][settings["language"]]
        + cpt.vertical_datum
    )
    y_label_inclination = settings["vertical_settings"]["y_label_inclination"][
        settings["language"]
    ]
    tick_distance_depth = settings["vertical_settings"]["depth_tick_distance"]
    ticks_depth = np.arange(ylim[1], ylim[0], tick_distance_depth)

    # tick_locations_inclination, tick_labels_inclination = define_inclination_ticks_and_labels(
    #     cpt, depth, inclination, ylim, settings)

    # set depth axis
    ax.set_ylim(ylim)  # depth
    ax.set_ylabel(y_label_depth)
    ax.set_yticks(ticks_depth)
    ax.invert_yaxis()

    # set inclination axis if inclination is present
    if tick_labels_inclination:
        ax2 = ax.twinx()
        ax2.set_ylim(ylim)
        ax2.set_yticks(tick_locations_inclination)
        ax2.set_yticklabels(tick_labels_inclination)
        ax2.set_ylabel(y_label_inclination)
        ax2.invert_yaxis()


def __add_text_in_rectangle(ax, text, rectangle, rel_vertical_position, hor_spacing):
    """
    Adds text into rectangles

    :param ax: current axis
    :param text: text to be added
    :param rectangle: current rectangle
    :param rel_vertical_position: relative vertical position of text in rectangle
    :param hor_spacing: horizontal spacing of the text from the left side of the rectangle
    :return:
    """
    ax.annotate(
        text,
        (
            rectangle.xy[0] + hor_spacing,
            rectangle.xy[1] + rel_vertical_position * ax.patches[-1]._height,
        ),
        annotation_clip=False,
        fontsize=9,
    )


def create_bro_information_box(ax, scale, cpt, plot_nr, ylims, distance_from_plot):
    """

    :param ax: current axis
    :param scale: scale of the plot on the paper
    :param cpt: cpt data
    :param plot_nr: number of the plot within the current cpt data
    :param ylims: all vertical limits for the current cpt data
    :return:
    """
    from datetime import date

    # Sets text
    if cpt.plot_settings.general_settings["language"] == "Nederlands":
        cpt_type_txt = "Conustype: "
        norm_txt = "Norm: "
        class_txt = "Klasse: "
        page_txt = "Page: "
        date_measurement_txt = "Datum meting: "
        date_plot_txt = "Datum plot: "
    else:
        cpt_type_txt = "Cone type: "
        norm_txt = "Norm: "
        class_txt = "class: "
        page_txt = "Page: "
        date_measurement_txt = "Date result: "
        date_plot_txt = "Date plot: "

    y_min = ylims[plot_nr][1]
    y_max = ylims[plot_nr][0]

    height_box = 3.5 * scale  # [m]

    xmin = ax.dataLim.x0
    xmax = ax.dataLim.x1

    total_width = xmax - xmin

    cpt_number_box = Rectangle(
        (xmin, y_max + height_box + distance_from_plot + height_box * 3 / 4),
        total_width * 2 / 3,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    norm_box = Rectangle(
        (xmin, y_max + height_box + distance_from_plot + height_box * 2 / 4),
        total_width * 1 / 2,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    cpt_type_box = Rectangle(
        (xmin, y_max + height_box + distance_from_plot + height_box * 1 / 4),
        total_width * 1 / 2,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    cpt_class_box = Rectangle(
        (xmin, y_max + height_box + distance_from_plot + height_box * 0 / 4),
        total_width * 1 / 2,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    coordinate_box = Rectangle(
        (
            xmin + total_width * 3 / 6,
            y_max + height_box + distance_from_plot + height_box * 1 / 4,
        ),
        total_width * 1 / 6,
        height_box * 2 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )
    page_box = Rectangle(
        (
            xmin + total_width * 3 / 6,
            y_max + height_box + distance_from_plot + height_box * 0 / 4,
        ),
        total_width * 1 / 6,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    cpt_date_box = Rectangle(
        (
            xmin + total_width * 2 / 3,
            y_max + height_box + distance_from_plot + height_box * 3 / 4,
        ),
        total_width * 1 / 3,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )
    plot_data_box = Rectangle(
        (
            xmin + total_width * 2 / 3,
            y_max + height_box + distance_from_plot + height_box * 2 / 4,
        ),
        total_width * 1 / 3,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    empty_box = Rectangle(
        (
            xmin + total_width * 2 / 3,
            y_max + height_box + distance_from_plot + height_box * 0 / 4,
        ),
        total_width * 1 / 3,
        height_box * 2 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    hor_spacing = (xmax - xmin) / 100

    ax.add_patch(cpt_number_box)
    __add_text_in_rectangle(ax, "Bro id: " + cpt.name, ax.patches[-1], 1 / 2, hor_spacing)

    ax.add_patch(norm_box)
    __add_text_in_rectangle(
        ax, norm_txt + cpt.cpt_standard, ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(cpt_type_box)
    __add_text_in_rectangle(
        ax, cpt_type_txt + cpt.cpt_type, ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(cpt_class_box)
    __add_text_in_rectangle(
        ax, class_txt + cpt.quality_class, ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(coordinate_box)
    __add_text_in_rectangle(
        ax,
        "x = " + "{:.1f}".format(cpt.coordinates[0]),
        ax.patches[-1],
        2 / 3,
        hor_spacing,
    )
    __add_text_in_rectangle(
        ax,
        "y = " + "{:.1f}".format(cpt.coordinates[1]),
        ax.patches[-1],
        1 / 3,
        hor_spacing,
    )

    ax.add_patch(page_box)
    __add_text_in_rectangle(
        ax,
        page_txt + str(plot_nr + 1) + "/" + str(len(ylims)),
        ax.patches[-1],
        1 / 2,
        hor_spacing,
    )

    ax.add_patch(cpt_date_box)
    __add_text_in_rectangle(
        ax, date_measurement_txt + cpt.result_time, ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(plot_data_box)
    __add_text_in_rectangle(
        ax, date_plot_txt + str(date.today()), ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(empty_box)


def create_gef_information_box(ax, scale, cpt, plot_nr, ylims):
    """
    Sets textboxes with meta data

    :param ax: current axis
    :param scale: scale of the plot on the paper
    :param cpt: cpt data
    :param plot_nr: number of the plot within the current cpt data
    :param ylims: all vertical limits for the current cpt data
    :return:
    """
    from datetime import date

    # Sets text
    if cpt.plot_settings.general_settings["language"] == "Nederlands":
        cpt_type_txt = "Conustype: "
        norm_and_class_txt = "Norm en klasse: "
        page_txt = "Page: "
        date_measurement_txt = "Datum meting: "
        date_plot_txt = "Datum plot: "
    else:
        cpt_type_txt = "Cone type: "
        norm_and_class_txt = "Norm and class: "
        page_txt = "Page: "
        date_measurement_txt = "Date result: "
        date_plot_txt = "Date plot: "

    y_min = ylims[plot_nr][1]
    y_max = ylims[plot_nr][0]

    y_tick_size = (y_max - y_min) / ax.yaxis.major.formatter.axis.major.locator.locs.size

    height_box = 3.5 * y_tick_size * scale  # [m]
    distance_from_plot = -1

    xmin = ax.dataLim.x0
    xmax = ax.dataLim.x1

    total_width = xmax - xmin

    cpt_number_box = Rectangle(
        (xmin, y_max + height_box + distance_from_plot + height_box * 3 / 4),
        total_width * 2 / 4,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    cpt_type_box = Rectangle(
        (xmin, y_max + height_box + distance_from_plot + height_box * 2 / 4),
        total_width * 1 / 2,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    cpt_class_box = Rectangle(
        (xmin, y_max + height_box + distance_from_plot + height_box * 1 / 4),
        total_width * 2 / 2,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    coordinate_box = Rectangle(
        (
            xmin + total_width * 3 / 6,
            y_max + height_box + distance_from_plot + height_box * 2 / 4,
        ),
        total_width * 1 / 6,
        height_box * 2 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )
    page_box = Rectangle(
        (
            xmin + total_width * 5 / 6,
            y_max + height_box + distance_from_plot + height_box * 0 / 4,
        ),
        total_width * 1 / 6,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    cpt_date_box = Rectangle(
        (
            xmin + total_width * 2 / 3,
            y_max + height_box + distance_from_plot + height_box * 3 / 4,
        ),
        total_width * 1 / 3,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )
    plot_data_box = Rectangle(
        (
            xmin + total_width * 2 / 3,
            y_max + height_box + distance_from_plot + height_box * 2 / 4,
        ),
        total_width * 1 / 3,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    empty_box = Rectangle(
        (
            xmin + total_width * 0 / 6,
            y_max + height_box + distance_from_plot + height_box * 0 / 4,
        ),
        total_width * 5 / 6,
        height_box * 1 / 4,
        facecolor="none",
        clip_on=False,
        edgecolor="black",
    )

    hor_spacing = (xmax - xmin) / 100

    ax.add_patch(cpt_number_box)
    __add_text_in_rectangle(ax, "Gef id: " + cpt.name, ax.patches[-1], 1 / 2, hor_spacing)

    ax.add_patch(cpt_type_box)
    __add_text_in_rectangle(
        ax, cpt_type_txt + cpt.cpt_type, ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(cpt_class_box)
    __add_text_in_rectangle(
        ax, norm_and_class_txt + cpt.quality_class, ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(coordinate_box)
    __add_text_in_rectangle(
        ax,
        "x = " + "{:.1f}".format(cpt.coordinates[0]),
        ax.patches[-1],
        2 / 3,
        hor_spacing,
    )
    __add_text_in_rectangle(
        ax,
        "y = " + "{:.1f}".format(cpt.coordinates[1]),
        ax.patches[-1],
        1 / 3,
        hor_spacing,
    )

    ax.add_patch(page_box)
    __add_text_in_rectangle(
        ax,
        page_txt + str(plot_nr + 1) + "/" + str(len(ylims)),
        ax.patches[-1],
        1 / 2,
        hor_spacing,
    )

    ax.add_patch(cpt_date_box)
    __add_text_in_rectangle(
        ax, date_measurement_txt + cpt.result_time, ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(plot_data_box)
    __add_text_in_rectangle(
        ax, date_plot_txt + str(date.today()), ax.patches[-1], 1 / 2, hor_spacing
    )

    ax.add_patch(empty_box)


def create_information_box(ax, scale, cpt, plot_nr, ylims, distance_from_plot):
    if cpt.__class__.__name__ == "BroXmlCpt":
        create_bro_information_box(ax, scale, cpt, plot_nr, ylims, distance_from_plot)
    elif cpt.__class__.__name__ == "GefCpt":
        create_gef_information_box(ax, scale, cpt, plot_nr, ylims)


def set_figure_size(fig, ylim):
    """
    Sets the figure size in inches

    :param fig: current figure
    :param ylim: current vertical limit
    :return:
    """
    # set size in inches
    size_landscape = [
        A4_WIDTH,
        A4_LENGTH / CALIBRATED_LENGTH_FIGURE_SIZE * (ylim[0] - ylim[1]),
    ]
    fig.set_size_inches(size_landscape[0], size_landscape[1])
