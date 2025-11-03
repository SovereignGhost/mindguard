"""Phase 3: Build Decision Dependence Graph.

Implements Gaussian-weighted layer aggregation, two-stage attention sink
filter, Total Attention Energy (TAE) edge scoring, and a minimal DDG graph
structure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


def gaussian_weights(num_layers: int) -> List[float]:
    """Return Gaussian weights emphasizing middle layers."""
    if num_layers <= 0:
        return []
    sigma = num_layers / 6.0
    mid = (num_layers - 1) / 2.0
    weights = [
        math.exp(-((layer_idx - mid) ** 2) / (2 * sigma * sigma)) for layer_idx in range(num_layers)
    ]
    s = sum(weights)
    return [w / s for w in weights]


def combine_layers(attentions: Any) -> Any:
    """Combine layer attentions using Gaussian weights.

    Expects attentions with shape (layers, heads, seq_len, seq_len) or a list-like.
    """
    layers = len(attentions)
    w = gaussian_weights(layers)
    combined = None
    for i, layer in enumerate(attentions):
        layer_sum = layer.sum(dim=0)  # sum over heads → (seq_len, seq_len)
        weighted = layer_sum * w[i]
        combined = weighted if combined is None else combined + weighted
    return combined  # (seq_len, seq_len)


def _top_k_tokens(total_attn, k: int) -> List[int]:
    import torch

    k = min(k, total_attn.numel())
    _vals, idx = torch.topk(total_attn, k)
    return list(idx.tolist())


def filter_attention_sinks(attn_mat: Any, k: int = 80, epsilon: float = 0.85) -> Any:
    """Two-stage sink filter.

    Stage 1: compute total attention received by each token and select top-k.
    Stage 2: for each selected token, compute normalized entropy across sources;
             if higher than epsilon, zero out that column.
    """
    seq_len = attn_mat.shape[0]
    total = attn_mat.sum(dim=0)  # attention received by each token (seq_len,)
    top_idx = _top_k_tokens(total, k)

    for j in top_idx:
        col = attn_mat[:, j]
        denom = col.sum()
        if denom <= 0:
            continue
        probs = col / denom
        # entropy in nats then normalize by log(n)
        entropy = -(probs * (probs + 1e-12).log()).sum()
        norm_entropy = entropy / math.log(seq_len + 1e-12)
        if norm_entropy > epsilon:
            attn_mat[:, j] = 0.0
    return attn_mat


def compute_tae(submatrix: Any) -> float:
    """Total Attention Energy (squared sum)."""
    return float((submatrix**2).sum().item())


@dataclass
class DDG:
    """Minimal DDG structure with vertex token spans and weighted edges."""

    vertices: Dict[str, List[int]]
    edges: Dict[Tuple[str, str], float]

    def get_weight(self, source: str, target: str) -> float:
        """Return edge weight from source to target, or 0.0 if absent."""
        return self.edges.get((source, target), 0.0)

    @property
    def uninvoked_tools(self) -> List[str]:
        """List tool vertices (prefixed with 'tool:')."""
        return [v for v in self.vertices.keys() if v.startswith("tool:")]


def build_ddg(
    attentions: Any, vertices: Dict[str, List[int]], k: int = 80, epsilon: float = 0.85
) -> DDG:
    """Construct a DDG from attentions and vertex token spans."""
    import torch

    combined = combine_layers(attentions)  # (seq_len, seq_len)
    filtered = filter_attention_sinks(combined.clone(), k=k, epsilon=epsilon)

    edges: Dict[Tuple[str, str], float] = {}
    # Compute edge weight as TAE between source span (rows) and target span (cols)
    for src_name, src_idx in vertices.items():
        for tgt_name, tgt_idx in vertices.items():
            if src_name == tgt_name:
                continue
            sub = filtered[torch.tensor(src_idx)[:, None], torch.tensor(tgt_idx)]
            edges[(src_name, tgt_name)] = compute_tae(sub)

    return DDG(vertices=vertices, edges=edges)


__all__ = [
    "gaussian_weights",
    "combine_layers",
    "filter_attention_sinks",
    "compute_tae",
    "DDG",
    "build_ddg",
]
