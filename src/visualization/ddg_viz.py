"""Phase 4: Graph visualization.

Utilities to visualize a DDG using NetworkX + Plotly.
"""

from __future__ import annotations

import networkx as nx
import plotly.graph_objects as go


def ddg_to_networkx(ddg) -> nx.DiGraph:
    """Convert DDG to NetworkX directed graph."""
    G = nx.DiGraph()
    for v in ddg.vertices.keys():
        G.add_node(v)
    for (src, tgt), w in ddg.edges.items():
        if w > 0:
            G.add_edge(src, tgt, weight=w)
    return G


def plot_ddg(ddg, highlight_source: str | None = None) -> go.Figure:
    """Create an interactive Plotly figure for a DDG graph."""
    G = ddg_to_networkx(ddg)
    pos = nx.spring_layout(G, seed=42)

    edge_x = []
    edge_y = []
    edge_w = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_w.append(data.get("weight", 0.0))

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line={"width": 1, "color": "#888"},
        hoverinfo="none",
        mode="lines",
    )

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        if node == "user_query":
            node_color.append("#1f77b4")  # blue
        elif node.startswith("tool:"):
            node_color.append("#2ca02c")  # green
        elif node in ("invoked_tool_name", "invoked_params", "invoked_tool"):
            node_color.append("#ff7f0e")  # orange
        else:
            node_color.append("#7f7f7f")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hoverinfo="text",
        marker={"color": node_color, "size": 12, "line": {"width": 1, "color": "#333"}},
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Decision Dependence Graph",
        showlegend=False,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig


__all__ = ["ddg_to_networkx", "plot_ddg"]
