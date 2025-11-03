"""Phase 3: Extract logical concepts from LLM context.

Heuristic parser that extracts vertex token indices for:
  - v_u: user query tokens ("user_query")
  - v_t: tool description tokens (per tool, key: "tool:<name>")
  - v_c_t: invoked tool name tokens ("invoked_tool_name")
  - v_c_p: invoked parameter tokens ("invoked_params")

Inputs are the rendered MCP text context, the generated LLM output text,
and tokenized context (ids → tokens) from the wrapper. This implementation is
format-aware for the context produced by MCPContextBuilder.serialize_text().
"""

from __future__ import annotations

import re
from typing import Dict, List


def _token_spans(
    token_text: List[str], start_char: int, end_char: int, joined: str, offsets: List[int]
) -> List[int]:
    """Map character span to token indices using precomputed offsets."""
    span: List[int] = []
    for _i, off in enumerate(offsets):
        tok_start = off
        tok_end = off + len(token_text[_i])
        if tok_end > start_char and tok_start < end_char:
            span.append(_i)
    return span


def _compute_char_offsets(token_text: List[str]) -> List[int]:
    """Compute naive char offsets by joining tokens with spaces.

    Assumes tokenizer joined by single spaces. For accurate mapping use
    Hugging Face provided offset mappings; this is a lightweight fallback.
    """
    offsets: List[int] = []
    pos = 0
    for _i, tok in enumerate(token_text):
        offsets.append(pos)
        # add space after each token except the last; caller uses joined string
        pos += len(tok) + 1
    return offsets


def parse_context(
    context_text: str, output_text: str, token_text: List[str]
) -> Dict[str, List[int]]:
    """Extract vertex token indices from context and output text.

    Args:
        context_text: The full textual context given to the model.
        output_text: The model's generated text (tool invocation).
        token_text: Token strings corresponding to the tokenization of context_text.

    Returns:
        Dict mapping vertex names to lists of token indices.
    """
    # Precompute helpers
    joined = " ".join(token_text)
    offsets = _compute_char_offsets(token_text)

    vertices: Dict[str, List[int]] = {}

    # v_u: user query (assumes line starting with 'User: ')
    m_user = re.search(r"^User:\s*(.*)$", context_text, flags=re.MULTILINE)
    if m_user:
        uq = m_user.group(1)
        start = context_text.find(uq)
        end = start + len(uq)
        vertices["user_query"] = _token_spans(token_text, start, end, joined, offsets)
    else:
        vertices["user_query"] = []

    # v_t: each tool block line '- <name>: <description>' and next 'params: {...}'
    tool_blocks = re.findall(r"^-\s*(\w+):\s*(.*)$", context_text, flags=re.MULTILINE)
    for name, desc in tool_blocks:
        # span over description only (name influences name parsing elsewhere)
        start = context_text.find(desc)
        end = start + len(desc)
        vertices[f"tool:{name}"] = _token_spans(token_text, start, end, joined, offsets)

    # v_c_t and v_c_p from output text heuristics: name(...) and args JSON-like
    # Try patterns like: invoke_tool(name='ReadFile', args={...}) or plain 'ReadFile(' and '{...}'
    v_ct: List[int] = []
    v_cp: List[int] = []

    m_name = re.search(r"name\s*=\s*['\"]([A-Za-z0-9_]+)['\"]|([A-Za-z0-9_]+)\s*\(", output_text)
    if m_name:
        tool_name = m_name.group(1) or m_name.group(2)
        # Locate the tool name occurrence in context within the tools list to map tokens
        ctx_name_pos = context_text.find(f"- {tool_name}:")
        if ctx_name_pos == -1:
            ctx_name_pos = context_text.find(tool_name)
        if ctx_name_pos != -1:
            v_ct = _token_spans(
                token_text, ctx_name_pos, ctx_name_pos + len(tool_name), joined, offsets
            )

    m_args = re.search(r"args\s*=\s*(\{.*\})|\((.*)\)", output_text)
    if m_args:
        args_str = m_args.group(1) or m_args.group(2) or ""
        # Try to map any literal substrings (paths, emails) into context; fallback empty
        # Find first quoted string inside args and map
        m_lit = re.search(r"['\"]([^'\"]+)['\"]", args_str)
        if m_lit:
            lit = m_lit.group(1)
            pos = context_text.find(lit)
            if pos != -1:
                v_cp = _token_spans(token_text, pos, pos + len(lit), joined, offsets)

    vertices["invoked_tool_name"] = v_ct
    vertices["invoked_params"] = v_cp

    # helper vertex label used by defender denominator
    # choose the tool that best matches invoked name as 'invoked_tool'
    if v_ct:
        # find tool name text from context around the first token index
        vertices["invoked_tool"] = v_ct
    else:
        vertices["invoked_tool"] = []

    return vertices


__all__ = ["parse_context"]
