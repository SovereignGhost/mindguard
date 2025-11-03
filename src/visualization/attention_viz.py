"""Phase 4: Attention heatmaps.

Plot attention matrices and before/after sink filtering comparisons.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import plotly.express as px


def heatmap(attn: Any, title: str = "Attention"):
    """Plot a heatmap for a 2D attention matrix."""
    arr = attn.detach().cpu().numpy() if hasattr(attn, "detach") else np.array(attn)
    fig = px.imshow(arr, color_continuous_scale="Viridis", title=title)
    fig.update_layout(margin={"l": 20, "r": 20, "t": 40, "b": 20})
    return fig


__all__ = ["heatmap"]
