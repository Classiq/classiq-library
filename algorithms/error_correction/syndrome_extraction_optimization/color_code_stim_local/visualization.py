from typing import TYPE_CHECKING, List, Optional, Tuple

import igraph as ig
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.patches import Polygon as mpl_Polygon
from matplotlib.ticker import AutoLocator

# Use TYPE_CHECKING for type hints without runtime imports
if TYPE_CHECKING:
    from .color_code import ColorCode


def draw_lattice(
    code: "ColorCode",
    ax: Optional[plt.Axes] = None,
    show_axes: bool = False,
    edge_color: str = "black",
    edge_linewidth: float = 1.0,
    face_lightness: float = 0.3,
    show_data_qubits: bool = True,
    data_qubit_color: str = "black",
    data_qubit_size: float = 100.0,
    highlight_qubits: Optional[
        List[int] | List[Tuple[float, float]] | List[str] | np.ndarray
    ] = None,
    highlight_qubit_color: str = "orange",
    highlight_qubit_marker: str = "^",
    highlight_qubits2: Optional[
        List[int] | List[Tuple[float, float]] | List[str] | np.ndarray
    ] = None,
    highlight_qubit_color2: str = "purple",
    highlight_qubit_marker2: str = "s",
    highlight_faces: Optional[
        List[int] | List[Tuple[float, float]] | List[str] | np.ndarray
    ] = None,
    highlight_face_lightness: float = 1,
    figsize: Tuple[float, float] = (6, 5),
) -> plt.Axes:
    """
    Draws the color code lattice.

    Parameters
    ----------
    code : ColorCode
        The ColorCode object containing the Tanner graph.
    ax : matplotlib.axes.Axes, optional
        The axis on which to draw the graph. If None, a new figure and
        axis will be created.
    show_axes : bool, default False
        Whether to show the x- and y-axis.
    edge_color : str, default 'black'
        Colors for edges.
    edge_linewidth : float, default 1.0
        Linewidth for edges.
    face_lightness : float, default 0.3
        Controls the lightness of face colors. Lower values make colors lighter.
    show_data_qubits : bool, default True
        Whether to draw circles representing data qubits.
    data_qubit_color : str, default 'black'
        Color for the data qubit circles (if shown).
    data_qubit_size : float, default 100.0
        Size for the data qubit circles (if shown).
    highlight_qubits : list[int] | list[tuple] | list[str] | np.ndarray, optional
        Data qubits to highlight with orange triangles (by default).
        Can be a list of data qubit indices (ordered by code.vs.select(pauli=None)),
        a list of coordinate tuples [(x, y), ...], or a list of qubit names ['x-y', ...].
    highlight_qubit_color : str, default 'orange'
        The color used to highlight specified data qubits.
    highlight_qubit_marker : str, default '^' (triangle)
        The marker used to highlight specified data qubits.
    highlight_qubits2 : list[int] | list[tuple] | list[str] | np.ndarray, optional
        Data qubits to highlight with purple squares (by default).
        Format is the same as highlight_qubits.
    highlight_qubit_color2 : str, default 'purple'
        The color used to highlight the second set of specified data qubits.
    highlight_qubit_marker2 : str, default 's' (square)
        The marker used to highlight the second set of specified data qubits.
    highlight_faces : list[int] | list[tuple] | list[str] | np.ndarray, optional
        Z ancillary qubits whose corresponding faces should be highlighted.
        Can be a list of Z ancillary qubit indices (ordered by code.vs.select(pauli="Z")),
        a list of coordinate tuples [(x, y), ...], or a list of qubit names ['x-y', ...].
        Note that for names, the actual stored name includes a '-Z' suffix.
    highlight_face_lightness : float, default 0.7
        Controls the lightness of highlighted faces. Higher values make colors more vibrant.

    Returns
    -------
    matplotlib.axes.Axes
        The axis containing the drawn lattice visualization.
    """
    if ax is None:
        # figsize is set when calling plt.subplots(), not here directly
        fig, ax = plt.subplots(figsize=figsize)

    graph = code.tanner_graph
    data_qubits = graph.vs.select(pauli=None)
    anc_Z_qubits = graph.vs.select(pauli="Z")

    # --- Pre-process highlight_qubits ---
    highlight_indices = set()
    if isinstance(highlight_qubits, np.ndarray):
        highlight_qubits = highlight_qubits.tolist()
    if highlight_qubits:
        coords_to_vid = {(v["x"], v["y"]): v.index for v in data_qubits}
        name_to_vid = {v["name"]: v.index for v in data_qubits}
        data_qubit_indices = [
            v.index for v in data_qubits
        ]  # For index-based highlighting

        for hq in highlight_qubits:
            found_vid = None
            if isinstance(hq, int):
                if 0 <= hq < len(data_qubit_indices):
                    found_vid = data_qubit_indices[hq]
                else:
                    print(f"Warning: Highlight index {hq} is out of range.")
            elif isinstance(hq, tuple) and len(hq) == 2:
                found_vid = coords_to_vid.get(hq)
                if found_vid is None:
                    print(f"Warning: Highlight coordinate {hq} not found.")
            elif isinstance(hq, str):
                found_vid = name_to_vid.get(hq)
                if found_vid is None:
                    print(f"Warning: Highlight name '{hq}' not found.")
            else:
                print(f"Warning: Invalid highlight format: {hq}. Skipping.")

            if found_vid is not None:
                highlight_indices.add(found_vid)

    # --- Pre-process highlight_qubits2 ---
    highlight_indices2 = set()
    if isinstance(highlight_qubits2, np.ndarray):
        highlight_qubits2 = highlight_qubits2.tolist()
    if highlight_qubits2:
        coords_to_vid = {(v["x"], v["y"]): v.index for v in data_qubits}
        name_to_vid = {v["name"]: v.index for v in data_qubits}
        data_qubit_indices = [
            v.index for v in data_qubits
        ]  # For index-based highlighting

        for hq in highlight_qubits2:
            found_vid = None
            if isinstance(hq, int):
                if 0 <= hq < len(data_qubit_indices):
                    found_vid = data_qubit_indices[hq]
                else:
                    print(f"Warning: Highlight index {hq} is out of range.")
            elif isinstance(hq, tuple) and len(hq) == 2:
                found_vid = coords_to_vid.get(hq)
                if found_vid is None:
                    print(f"Warning: Highlight coordinate {hq} not found.")
            elif isinstance(hq, str):
                found_vid = name_to_vid.get(hq)
                if found_vid is None:
                    print(f"Warning: Highlight name '{hq}' not found.")
            else:
                print(f"Warning: Invalid highlight format: {hq}. Skipping.")

            if found_vid is not None:
                highlight_indices2.add(found_vid)

    # --- Pre-process highlight_faces ---
    highlight_face_indices = set()
    if isinstance(highlight_faces, np.ndarray):
        highlight_faces = highlight_faces.tolist()
    if highlight_faces:
        z_coords_to_vid = {(v["x"], v["y"]): v.index for v in anc_Z_qubits}
        z_name_to_vid = {v["name"]: v.index for v in anc_Z_qubits}
        # For Z qubits with name format "x-y", also add a mapping for "x-y-Z"
        z_name_to_vid.update(
            {
                n.replace("-Z", ""): idx
                for n, idx in z_name_to_vid.items()
                if n.endswith("-Z")
            }
        )
        z_qubit_indices = [
            v.index for v in anc_Z_qubits
        ]  # For index-based highlighting

        for hf in highlight_faces:
            found_vid = None
            if isinstance(hf, int):
                if 0 <= hf < len(z_qubit_indices):
                    found_vid = z_qubit_indices[hf]
                else:
                    print(f"Warning: Highlight face index {hf} is out of range.")
            elif isinstance(hf, tuple) and len(hf) == 2:
                found_vid = z_coords_to_vid.get(hf)
                if found_vid is None:
                    print(f"Warning: Highlight face coordinate {hf} not found.")
            elif isinstance(hf, str):
                # Try with and without the "-Z" suffix
                found_vid = z_name_to_vid.get(hf)
                if found_vid is None:
                    print(f"Warning: Highlight face name '{hf}' not found.")
            else:
                print(f"Warning: Invalid highlight face format: {hf}. Skipping.")

            if found_vid is not None:
                highlight_face_indices.add(found_vid)

    # --- Color mapping ---
    color_map = {"r": "red", "g": "green", "b": "blue"}

    # Function to lighten a color based on alpha value
    def lighten_color(color: str, alpha_factor: float) -> Tuple[float, float, float]:
        """
        Return a lighter version of ``color`` controlled by ``alpha_factor``.

        Parameters
        ----------
        color : str
            Matplotlib-compatible color specification.
        alpha_factor : float
            Value in ``[0, 1]`` controlling the blend with white. ``0`` yields the
            lightest color.

        Returns
        -------
        r, g, b : 3-tuple of float
            Lightened RGB color values.
        """

        r, g, b = to_rgb(color)
        r = r + (1 - r) * (1 - alpha_factor)
        g = g + (1 - g) * (1 - alpha_factor)
        b = b + (1 - b) * (1 - alpha_factor)
        return (r, g, b)

    # --- Draw Polygons ---
    all_coords = []
    for anc_z in anc_Z_qubits:
        anc_color_label = anc_z["color"]
        base_color = color_map.get(anc_color_label, "gray")

        # Use highlight_face_lightness for highlighted faces
        if anc_z.index in highlight_face_indices:
            current_lightness = highlight_face_lightness
        else:
            current_lightness = face_lightness

        # Lighten the color based on alpha but keep opacity at 1
        fill_color = lighten_color(base_color, current_lightness)

        neighbors = [v for v in anc_z.neighbors() if v["pauli"] is None]

        if len(neighbors) < 3:
            continue

        ordered_vertices = []
        if neighbors:
            visited_edges = set()
            current_dq = neighbors[0]
            ordered_vertices.append(current_dq)
            remaining_neighbors = set(neighbors[1:])

            while len(ordered_vertices) < len(neighbors):
                found_next = False
                for edge_id in graph.incident(current_dq, mode="all"):
                    edge = graph.es[edge_id]
                    if edge["kind"] == "lattice" and edge.index not in visited_edges:
                        other_vertex_index = (
                            edge.target
                            if edge.source == current_dq.index
                            else edge.source
                        )
                        other_vertex = graph.vs[other_vertex_index]
                        if other_vertex in remaining_neighbors:
                            ordered_vertices.append(other_vertex)
                            remaining_neighbors.remove(other_vertex)
                            visited_edges.add(edge.index)
                            current_dq = other_vertex
                            found_next = True
                            break
                if not found_next:
                    break

        if len(ordered_vertices) < 3:
            continue

        polygon_coords = [(v["x"], v["y"]) for v in ordered_vertices]
        all_coords.extend(polygon_coords)

        polygon = mpl_Polygon(
            polygon_coords,
            closed=True,
            edgecolor=edge_color,
            facecolor=fill_color,
            linewidth=edge_linewidth,
            alpha=1.0,  # Fully opaque
            zorder=1,  # Draw polygons behind qubits
        )
        ax.add_patch(polygon)

    # --- Draw Data Qubits ---
    if show_data_qubits:
        data_x = [v["x"] for v in data_qubits]
        data_y = [v["y"] for v in data_qubits]

        # Draw regular data qubits (those not highlighted)
        regular_indices = [
            i
            for i, v in enumerate(data_qubits)
            if v.index not in highlight_indices and v.index not in highlight_indices2
        ]
        if regular_indices:
            regular_x = [data_x[i] for i in regular_indices]
            regular_y = [data_y[i] for i in regular_indices]
            ax.scatter(
                regular_x,
                regular_y,
                c=data_qubit_color,
                s=data_qubit_size,
                edgecolors="none",
                linewidths=1,
                marker="o",
                zorder=2,
            )

        # Draw highlight_qubits with triangles (drawn last to appear on top)
        if highlight_indices:
            highlight1_indices = [
                i for i, v in enumerate(data_qubits) if v.index in highlight_indices
            ]
            highlight1_x = [data_x[i] for i in highlight1_indices]
            highlight1_y = [data_y[i] for i in highlight1_indices]
            ax.scatter(
                highlight1_x,
                highlight1_y,
                c=highlight_qubit_color,
                s=data_qubit_size * 1.2,  # Slightly larger for visibility
                edgecolors="black",
                linewidths=1,
                marker=highlight_qubit_marker,  # Triangle marker
                zorder=4,  # Higher zorder to appear on top of squares
            )

        # Draw highlight_qubits2 with squares
        if highlight_indices2:
            highlight2_indices = [
                i for i, v in enumerate(data_qubits) if v.index in highlight_indices2
            ]
            highlight2_x = [data_x[i] for i in highlight2_indices]
            highlight2_y = [data_y[i] for i in highlight2_indices]
            ax.scatter(
                highlight2_x,
                highlight2_y,
                c=highlight_qubit_color2,
                s=data_qubit_size * 1.2,  # Slightly larger for visibility
                edgecolors="black",
                linewidths=1,
                marker=highlight_qubit_marker2,  # Square marker
                zorder=3,
            )

        all_coords.extend(zip(data_x, data_y))

    # --- Final Axis Adjustments ---
    if all_coords:
        coords_array = np.array(all_coords)
        min_x, min_y = coords_array.min(axis=0)
        max_x, max_y = coords_array.max(axis=0)
        span_x = max_x - min_x
        span_y = max_y - min_y

        # Add padding based on each axis' span
        padding_factor = 0.1  # 10% padding
        padding_x = max(span_x * padding_factor, 1.0)  # Minimum padding
        padding_y = max(span_y * padding_factor, 1.0)  # Minimum padding

        ax.set_xlim(min_x - padding_x, max_x + padding_x)
        ax.set_ylim(min_y - padding_y, max_y + padding_y)

    # ax.set_aspect('equal', adjustable='box') # REMOVED or COMMENTED OUT

    # 'auto' lets the aspect ratio be determined by data limits and figure size
    # 'box' forces the box aspect ratio to match figsize, potentially distorting data scale
    # 'datalim' forces the data aspect ratio to match figsize, potentially leaving whitespace
    # Choose 'auto' or 'box' depending on desired behavior when figsize is not square
    # Let's try 'auto' first as it's the default. If the user wants the box forced
    # into the figsize shape, change to 'box'.
    ax.set_aspect("auto", adjustable="box")  # Allows aspect ratio to follow figsize

    if not show_axes:
        ax.axis("off")
    else:
        for spine in ax.spines.values():
            spine.set_visible(True)

    return ax


def draw_tanner_graph(
    code: "ColorCode",
    ax: Optional[plt.Axes] = None,
    show_axes: bool = False,
    show_lattice: bool = False,
    figsize: Tuple[float, float] = (6, 5),
    **kwargs,
) -> plt.Axes:
    """
    Draw the tanner graph of the code.

    Parameters
    ----------
    code : ColorCode
        The ColorCode object containing the Tanner graph.
    ax : matplotlib.axes.Axes, optional
        The axis on which to draw the graph. If None, a new figure and axis will be created.
    show_axes : bool, default False
        Whether to show the x- and y-axis.
    show_lattice : bool, default False
        Whether to show the lattice edges in addition to the tanner graph edges.
    figsize : tuple(float, float), default (6, 5)
        Figure size (width, height) in inches when creating a new figure.
    **kwargs : dict
        Additional keyword arguments to pass to igraph.plot.

    Returns
    -------
    matplotlib.axes.Axes
        The axis containing the drawn graph.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    tanner_graph = code.tanner_graph
    g: ig.Graph
    g = tanner_graph.subgraph(tanner_graph.vs.select(pauli_ne="X"))
    if not show_lattice:
        g = g.subgraph_edges(g.es.select(kind="tanner"))

    color_dict = {"r": "red", "g": "green", "b": "blue"}
    g.vs["color"] = ["black" if c is None else color_dict[c] for c in g.vs["color"]]
    if show_lattice:
        links = g.es.select(kind="lattice")
        links["color"] = [color_dict[c] for c in links["color"]]

    ig.plot(g, target=ax, **kwargs)
    if show_axes:
        ax.spines["top"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.xaxis.set_major_locator(AutoLocator())
        ax.yaxis.set_major_locator(AutoLocator())

    return ax
