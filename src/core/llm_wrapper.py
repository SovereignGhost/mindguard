"""Phase 3: LLM integration with attention.

Lightweight wrapper for Hugging Face transformers models to run inference with
``output_attentions=True`` and return tokenization artifacts plus attention
matrices needed by the DDG pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List


@dataclass
class InferenceResult:
    """Container for model outputs needed downstream."""

    tokens: List[int]
    token_text: List[str]
    output_text: str
    attentions: Any  # (layers, heads, seq_len, seq_len) tensor-like


class LLMWrapper:
    """Thin wrapper around transformers model and tokenizer.

    This class defers imports to runtime to avoid hard dependency errors when
    transformers/torch are not installed in the environment at documentation time.
    """

    def __init__(self, model_name: str) -> None:
        """Initialize wrapper with a model identifier."""
        self.model_name = model_name
        self.model: Any = None
        self.tokenizer: Any = None

    def load(self) -> None:
        """Load model and tokenizer with attentions enabled."""
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            output_attentions=True,
        )
        self.model.eval()

    def infer(self, context_text: str, max_new_tokens: int = 64) -> InferenceResult:
        """Run inference and return tokens, output text, and attentions."""
        import torch

        assert self.model is not None and self.tokenizer is not None, "Call load() first"
        inputs = self.tokenizer(context_text, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                output_attentions=True,
                return_dict_in_generate=True,
            )

        # Collect attentions from the last forward pass of the base model
        # When using generate with return_dict_in_generate=True, the attentions for
        # decoder steps are in `outputs.decoder_attentions` for some models; to keep
        # pipeline generic we fall back to model outputs if present.
        attentions = None
        if hasattr(outputs, "attentions") and outputs.attentions is not None:
            attentions = outputs.attentions

        tokens: List[int] = inputs["input_ids"][0].tolist()
        token_text: List[str] = self.tokenizer.convert_ids_to_tokens(tokens)
        output_ids = outputs.sequences[0].tolist()
        output_text = self.tokenizer.decode(output_ids[len(tokens) :], skip_special_tokens=True)

        return InferenceResult(
            tokens=tokens,
            token_text=token_text,
            output_text=output_text,
            attentions=attentions,
        )


__all__ = ["LLMWrapper", "InferenceResult"]
