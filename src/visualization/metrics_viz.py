"""Phase 4: Performance metrics.

Plot ROC and PR curves, and histograms for AIR distributions.
"""

from __future__ import annotations

from typing import Sequence

import plotly.graph_objects as go


def plot_roc(fpr: Sequence[float], tpr: Sequence[float], auc: float | None = None) -> go.Figure:
    """Plot ROC curve with optional AUC in the title."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", name="ROC"))
    fig.add_trace(
        go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Chance", line={"dash": "dash"})
    )
    title = "ROC Curve" if auc is None else f"ROC Curve (AUC={auc:.3f})"
    fig.update_layout(
        title=title, xaxis_title="False Positive Rate", yaxis_title="True Positive Rate"
    )
    return fig


def plot_pr(
    recall: Sequence[float], precision: Sequence[float], ap: float | None = None
) -> go.Figure:
    """Plot Precision-Recall curve with optional AP in the title."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recall, y=precision, mode="lines", name="PR"))
    title = "Precision-Recall Curve" if ap is None else f"Precision-Recall Curve (AP={ap:.3f})"
    fig.update_layout(title=title, xaxis_title="Recall", yaxis_title="Precision")
    return fig


def plot_hist(data: Sequence[float], title: str, nbins: int = 30) -> go.Figure:
    """Plot histogram for a numeric sequence."""
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=data, nbinsx=nbins))
    fig.update_layout(title=title, xaxis_title="Value", yaxis_title="Count")
    return fig


__all__ = ["plot_roc", "plot_pr", "plot_hist"]
