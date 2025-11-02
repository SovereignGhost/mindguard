# MindGuard

**Tool Poisoning Defense System for LLMs**

MindGuard is a defense mechanism that detects and attributes tool poisoning attacks in Large Language Model (LLM) systems using Decision Dependence Graphs (DDG) and attention analysis.

## Project Structure

```
mindguard/
├── src/
│   ├── core/              # Phase 3: DDG construction and defense
│   ├── attacks/           # Phase 2: Attack simulation
│   ├── visualization/     # Phase 4: Visualization tools
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── data/                  # Datasets (synthetic, real-world, mcptox)
├── notebooks/             # Analysis notebooks
├── demo/                  # Demo application
└── configs/               # Configuration files
```

## Features

- **Context Parsing**: Extract logical concepts from LLM context
- **DDG Construction**: Build Decision Dependence Graphs from attention patterns
- **Anomaly Detection**: Detect tool poisoning attacks using AIR (Attribution Influence Ratio)
- **Attack Simulation**: Generate synthetic poisoned and benign samples
- **Visualization**: Graph visualization, attention heatmaps, and performance metrics

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Development Phases

1. **Phase 1**: Project setup and structure
2. **Phase 2**: Attack simulation and MCP context builder
3. **Phase 3**: Core DDG construction and defense mechanisms
4. **Phase 4**: Visualization and metrics

## License

MIT License

