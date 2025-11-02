# MindGuard Architecture Documentation

This directory contains comprehensive architecture documentation for the MindGuard system.

## Documents

1. **[overview.md](./overview.md)**: High-level system architecture, design principles, and core modules
2. **[data_flow.md](./data_flow.md)**: End-to-end data flow, transformations, and processing pipeline
3. **[component_interaction.md](./component_interaction.md)**: Component diagrams, class structures, and interactions
4. **[logging.md](./logging.md)**: Logging framework design and usage patterns

## Quick Reference

### Core Modules
- **Context Parser**: Extracts logical vertices from LLM context
- **DDG Builder**: Constructs Decision Dependence Graph from attention
- **Anomaly-aware Defender**: Detects attacks and attributes sources

### Key Concepts
- **DDG (Decision Dependence Graph)**: Weighted directed graph modeling LLM reasoning
- **AIR (Anomaly Influence Ratio)**: Metric for detecting anomalous tool influence
- **TAE (Total Attention Energy)**: Squared attention sum for edge weights
- **Sink Filter**: Two-stage filter to remove noise from attention signals

### Processing Flow
```
Context → LLM Inference → Context Parser → DDG Builder → Defender → Verdict
```

## Architecture Decisions

1. **Attention-based tracking**: Uses empirical correlation between attention and tool invocations
2. **Gaussian layer weighting**: Prioritizes middle transformer layers
3. **Two-stage sink filtering**: Removes high-entropy attention tokens
4. **TAE aggregation**: Emphasizes stronger attention connections
5. **Control/data flow separation**: Distinguishes tool selection from parameter manipulation

## References

- Paper: [MindGuard: Tracking, Detecting, and Attributing MCP Tool Poisoning Attack via Decision Dependence Graph](https://arxiv.org/pdf/2508.20412)
- MCP Specification: Model Context Protocol standard

