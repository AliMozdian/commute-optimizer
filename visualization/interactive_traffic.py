"""
visualization/interactive_traffic.py
Interactive network visualizer with a dynamic time slider to observe traffic waves.
"""

from typing import Dict, Tuple, List, Any
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.text import Text
import networkx as nx

from core.graph import RoadNetwork
from core.congestion import CongestionModel


def format_minutes_to_time(minutes: float) -> str:
    """Converts minutes from midnight to HH:MM format."""
    total_min = int(round(minutes))
    hours = (total_min // 60) % 24
    mins = total_min % 60
    return f"{hours:02d}:{mins:02d}"


def launch_interactive_traffic_viewer(
    network: RoadNetwork,
    congestion_model: CongestionModel,
    t_min: float = 420.0,
    t_max: float = 600.0,
    t_step: float = 5.0
) -> None:
    """
    Renders an interactive road network where students can slide through the
    commute window to visualize dynamic bottleneck formation and delay waves.
    """
    g = nx.DiGraph()

    # Load node coordinates
    pos = {}
    has_coords = False
    for node_id in network.all_nodes():
        g.add_node(node_id)
        x, y = network.get_coordinates(node_id)
        if x != 0.0 or y != 0.0:
            has_coords = True
        pos[node_id] = (x, y)

    if not has_coords:
        pos = nx.spring_layout(g, seed=42)

    edges = [(u, v) for u, v, _ in network.all_edges()]
    for u, v in edges:
        g.add_edge(u, v)

    fig, ax = plt.subplots(figsize=(12, 8))
    plt.subplots_adjust(bottom=0.20)

    # Colormap: Green (Zero Traffic) -> Yellow -> Red (Heavy Traffic)
    # Using the modern Matplotlib colormap registry
    cmap = mpl.colormaps["RdYlGn_r"]
    norm = mcolors.Normalize(vmin=0.0, vmax=3.0)

    # Draw static nodes and labels
    nx.draw_networkx_nodes(
        g,
        pos,
        node_color="#ECEFF1",
        edgecolors="#263238",
        node_size=1400,
        linewidths=2.0,
        ax=ax
    )
    labels = {n: network.nodes[n].get("label", n) for n in g.nodes()}
    nx.draw_networkx_labels(g, pos, labels=labels, font_size=9, font_weight="bold", ax=ax)

    # Edge containers
    edge_artists: Dict[Tuple[str, str], Any] = {}
    edge_text_artists: Dict[Tuple[str, str], Text] = {}

    for u, v in edges:
        edge_patch = nx.draw_networkx_edges(
            g,
            pos,
            edgelist=[(u, v)],
            edge_color="green",
            arrows=True,
            arrowsize=20,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.08",
            width=3.0,
            ax=ax
        )
        edge_artists[(u, v)] = edge_patch

        # Compute midpoint position for text label
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        xm, ym = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        
        # Perpendicular offset for visibility on dual-direction edges
        dx, dy = x2 - x1, y2 - y1
        length = (dx**2 + dy**2)**0.5 + 1e-6
        offset_x, offset_y = -dy / length * 0.25, dx / length * 0.25

        txt = ax.text(
            xm + offset_x,
            ym + offset_y,
            "",
            fontsize=8,
            fontweight="bold",
            color="#212121",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85, edgecolor="#9E9E9E"),
            ha="center",
            va="center"
        )
        edge_text_artists[(u, v)] = txt

    ax.set_title(
        f"Dynamic Road Network Traffic | Time: {format_minutes_to_time(t_min)}",
        fontsize=13,
        fontweight="bold"
    )
    ax.axis("off")

    # Colorbar representation
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Congestion Multiplier $C_e(t)$", rotation=270, labelpad=15)

    # Matplotlib Slider Widget (using 4-tuple geometry to satisfy Pylance typing)
    slider_rect: Tuple[float, float, float, float] = (0.20, 0.08, 0.60, 0.04)
    ax_slider = fig.add_axes(slider_rect, facecolor="#E0E0E0")
    time_slider = Slider(
        ax=ax_slider,
        label="Departure Time: ",
        valmin=t_min,
        valmax=t_max,
        valinit=t_min,
        valstep=t_step,
        valfmt="%0.0f min"
    )

    def update(val: float) -> None:
        current_time = float(time_slider.val)
        time_str = format_minutes_to_time(current_time)

        for u, v in edges:
            base_time = network.get_base_time(u, v)
            multiplier = congestion_model.get_multiplier(u, v, current_time)
            dynamic_time = base_time * (1.0 + multiplier)

            # Update edge color dynamically
            color = cmap(norm(multiplier))
            patches = edge_artists[(u, v)]
            if isinstance(patches, list):
                for p in patches:
                    p.set_edgecolor(color)
            else:
                patches.set_edgecolor(color)

            # Update label text
            txt_label = f"{dynamic_time:.1f}m\n(+{int(multiplier * 100)}%)" if multiplier > 0.05 else f"{dynamic_time:.1f}m"
            edge_text_artists[(u, v)].set_text(txt_label)

        ax.set_title(
            f"Dynamic Road Network Traffic | Time: {time_str} ({current_time:.1f} min)",
            fontsize=13,
            fontweight="bold"
        )
        fig.canvas.draw_idle()

    # Initial paint and callback binding
    update(t_min)
    time_slider.on_changed(update)

    plt.show()
