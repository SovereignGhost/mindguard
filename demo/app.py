"""Gradio/Streamlit demo application.

Minimal Streamlit app to run MindGuard on a synthetic example.
"""

import json
from pathlib import Path

import streamlit as st

from src.attacks.mcp_simulator import MCPContextBuilder, ToolMetadata, ToolRegistry
from src.core.context_parser import parse_context
from src.core.ddg_builder import build_ddg
from src.core.defender import detect_poisoning
from src.visualization.ddg_viz import plot_ddg


def load_example() -> dict:
    example = Path("data/examples/poisoned_a1_example.json")
    with open(example, "r") as f:
        return json.load(f)


def main() -> None:
    st.set_page_config(page_title="MindGuard Demo", layout="wide")
    st.title("MindGuard Demo")

    data = load_example()
    st.sidebar.header("Example Controls")
    example_type = st.sidebar.selectbox("Example", ["Poisoned A1", "Benign"], index=0)
    if example_type == "Benign":
        with open("data/examples/benign_example.json", "r") as f:
            data = json.load(f)

    # Build registry and context
    registry = ToolRegistry()
    for t in data["tools"]:
        registry.register(ToolMetadata(**t))
    builder = MCPContextBuilder(registry)
    ctx = builder.build_context(data["user_query"], [t["name"] for t in data["tools"]])
    ctx_text = builder.serialize_text(ctx)

    st.subheader("Context")
    st.code(ctx_text)

    # Fake model output using expected invocation for demo
    tool_name = data["expected_invocation"]["tool_name"]
    args = data["expected_invocation"]["arguments"]
    output_text = f"invoke_tool(name='{tool_name}', args={json.dumps(args)})"

    # Tokenization surrogate: simple whitespace tokens
    token_text = ctx_text.split()

    vertices = parse_context(ctx_text, output_text, token_text)

    # Build a dummy attention matrix: identity as placeholder (for demo only)
    import torch

    seq_len = len(token_text)
    dummy_attn = torch.stack([
        torch.stack([torch.eye(seq_len) for _ in range(2)]) for _ in range(4)
    ])  # (layers=4, heads=2, L, L)

    ddg = build_ddg(dummy_attn, vertices)
    verdict = detect_poisoning(ddg)

    st.subheader("Detection Result")
    st.json(verdict)

    st.subheader("DDG Visualization")
    fig = plot_ddg(ddg)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()


