# Data Infrastructure Setup - Deliverable Documentation

## Overview

This deliverable completes **Task 1.3: Data Infrastructure** from Phase 1 of the MINDGUARD project plan. It provides a complete data directory structure, schemas, utilities, and management tools for the project.

## What's Included

### 1. Core Files

- **`data_setup.py`**: Main script that creates the entire data directory structure
- **`data_utils.py`**: Utility classes for data management (loading, validation, caching)
- **`setup_data_infrastructure.sh`**: Bash script for automated setup

### 2. Generated Structure

When you run the setup, the following directory structure is created:

```
data/
├── synthetic/              # Synthetic test cases
│   ├── benign/            # 50 legitimate scenarios
│   ├── poisoned/          # 50 attack scenarios
│   │   ├── A1_explicit_hijacking/
│   │   └── A2_parameter_manipulation/
│   └── raw/
├── real_world/            # Real-world data (future)
│   ├── benign/
│   └── attacks/
├── mcptox/                # MCPTox benchmark
│   ├── original/
│   └── processed/
├── processed/             # Train/val/test splits
│   ├── train/
│   ├── val/
│   └── test/
├── cache/                 # Cached outputs
│   ├── attention_matrices/
│   └── model_outputs/
├── results/               # Experimental results
│   ├── experiments/
│   ├── ablations/
│   └── visualizations/
├── schemas/               # JSON schemas
│   ├── tool_schema.json
│   ├── test_case_schema.json
│   └── attack_schema.json
├── configs/               # Configuration files
│   └── dataset_config.json
└── examples/              # Example data files
    ├── benign_example.json
    └── poisoned_a1_example.json
```

## Installation & Setup

### Prerequisites

- Python 3.9 or higher
- Basic Python packages (json, pathlib, dataclasses)

### Quick Setup

1. **Save all three files to your project directory:**
   - `data_setup.py`
   - `data_utils.py`
   - `setup_data_infrastructure.sh`

2. **Make the bash script executable:**
   ```bash
   chmod +x setup_data_infrastructure.sh
   ```

3. **Run the setup:**
   ```bash
   ./setup_data_infrastructure.sh
   ```

   Or directly with Python:
   ```bash
   python3 data_setup.py
   ```

### Verification

After setup, verify by running:
```bash
python3 data_utils.py
```

This will demonstrate the utility functions and validate the example data.

## Key Components

### 1. DataStructureBuilder (`data_setup.py`)

Creates the complete directory hierarchy and initializes the project.

**Methods:**
- `create_directory_structure()`: Creates all directories
- `create_schemas()`: Generates JSON validation schemas
- `create_readme_files()`: Adds documentation to each directory
- `create_config_templates()`: Creates configuration files
- `create_example_data()`: Generates example test cases
- `create_gitignore()`: Sets up git ignore patterns
- `setup_all()`: Runs complete setup

**Usage:**
```python
from data_setup import DataStructureBuilder

builder = DataStructureBuilder(base_path="./data")
config = builder.setup_all()
```

### 2. Data Classes (`data_utils.py`)

Structured data representations for type safety and validation.

#### Tool
```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    server: str = "UnknownServer"
```

#### ToolInvocation
```python
@dataclass
class ToolInvocation:
    tool_name: str
    arguments: Dict[str, Any]
```

#### TestCase
```python
@dataclass
class TestCase:
    id: str
    user_query: str
    tools: List[Tool]
    expected_invocation: ToolInvocation
    label: str  # "benign" or "poisoned"
    attack_type: str = "none"
    poisoned_tool_id: Optional[str] = None
    metadata: Dict[str, Any] = None
```

### 3. Utility Classes (`data_utils.py`)

#### DataLoader
Handles loading and saving test cases.

```python
loader = DataLoader(data_root="./data")

# Load single test case
test_case = loader.load_test_case(Path("data/examples/benign_example.json"))

# Load entire dataset
all_cases = loader.load_dataset("synthetic")

# Load specific split
test_split = loader.load_split("test")

# Get statistics
stats = loader.get_statistics(all_cases)
```

#### DataValidator
Validates test cases against schemas.

```python
validator = DataValidator()

# Validate test case
valid, errors = validator.validate_test_case(test_case)

# Validate individual tool
valid, errors = validator.validate_tool(tool)
```

#### CacheManager
Manages caching of model outputs and attention matrices.

```python
cache = CacheManager()

# Save attention matrix
cache.save_attention("test_001", "qwen-7b", attention_tensor)

# Load cached attention
attention = cache.load_attention("test_001", "qwen-7b")

# Save model output
cache.save_output("test_001", "qwen-7b", output_dict)

# Load cached output
output = cache.load_output("test_001", "qwen-7b")

# Clear cache
cache.clear_cache("all")  # or "attention" or "output"
```

#### DatasetSplitter
Creates train/validation/test splits.

```python
splitter = DatasetSplitter()

# Create stratified splits
all_cases = loader.load_dataset("synthetic")
splits = splitter.create_splits(
    all_cases,
    train_ratio=0.6,
    val_ratio=0.2,
    test_ratio=0.2,
    stratify=True
)

# Save splits to processed directory
splitter.save_splits(splits)
```

## Data Schemas

### Tool Schema
```json
{
  "type": "object",
  "required": ["name", "description", "parameters"],
  "properties": {
    "name": {"type": "string"},
    "description": {"type": "string"},
    "parameters": {"type": "object"},
    "server": {"type": "string"}
  }
}
```

### Test Case Schema
```json
{
  "type": "object",
  "required": ["id", "user_query", "tools", "expected_invocation", "label"],
  "properties": {
    "id": {"type": "string"},
    "user_query": {"type": "string"},
    "tools": {"type": "array"},
    "expected_invocation": {"type": "object"},
    "label": {"type": "string", "enum": ["benign", "poisoned"]},
    "attack_type": {"type": "string"},
    "poisoned_tool_id": {"type": "string"},
    "metadata": {"type": "object"}
  }
}
```

## Configuration

The default configuration is in `data/configs/dataset_config.json`:

```json
{
  "synthetic_dataset": {
    "benign_count": 50,
    "poisoned_count": 50,
    "attack_distribution": {
      "A1_explicit_hijacking": 25,
      "A2_parameter_manipulation": 25
    },
    "intensity_distribution": {
      "obvious": 0.3,
      "moderate": 0.4,
      "subtle": 0.3
    },
    "domains": {
      "filesystem": 15,
      "email": 10,
      "database": 10,
      "web": 10,
      "mixed": 5
    }
  },
  "split_ratios": {
    "train": 0.6,
    "val": 0.2,
    "test": 0.2
  },
  "cache_settings": {
    "enable_attention_cache": true,
    "enable_output_cache": true,
    "max_cache_size_gb": 10
  }
}
```

## Example Usage

### Creating a Test Case Programmatically

```python
from data_utils import Tool, ToolInvocation, TestCase, DataLoader

# Create tools
tools = [
    Tool(
        name="CreateDirectory",
        description="Creates a new directory at the specified path",
        parameters={"path": {"type": "string"}},
        server="FileSystemServer"
    ),
    Tool(
        name="ReadFile",
        description="Reads the contents of a file",
        parameters={"path": {"type": "string"}},
        server="FileSystemServer"
    )
]

# Create expected invocation
invocation = ToolInvocation(
    tool_name="CreateDirectory",
    arguments={"path": "/home/user/projects"}
)

# Create test case
test_case = TestCase(
    id="benign_001",
    user_query="Create a new directory called 'projects' in my home folder",
    tools=tools,
    expected_invocation=invocation,
    label="benign",
    metadata={"domain": "filesystem", "complexity": "simple"}
)

# Save test case
loader = DataLoader()
loader.save_test_case(test_case, Path("data/synthetic/benign/benign_001.json"))
```

### Loading and Analyzing Dataset

```python
from data_utils import DataLoader

loader = DataLoader()

# Load all synthetic data
dataset = loader.load_dataset("synthetic")

# Get statistics
stats = loader.get_statistics(dataset)
print(f"Total cases: {stats['total']}")
print(f"Benign: {stats['benign']}")
print(f"Poisoned: {stats['poisoned']}")
print(f"Attack types: {stats['attack_types']}")
print(f"Domains: {stats['domains']}")

# Filter poisoned cases
poisoned_cases = [tc for tc in dataset if tc.is_poisoned()]
print(f"\nPoisoned cases: {len(poisoned_cases)}")

for tc in poisoned_cases[:3]:  # Show first 3
    print(f"  {tc.id}: {tc.attack_type}")
    poisoned_tool = tc.get_poisoned_tool()
    if poisoned_tool:
        print(f"    Poisoned tool: {poisoned_tool.name}")
```

### Creating Splits

```python
from data_utils import DataLoader, DatasetSplitter

# Load data
loader = DataLoader()
dataset = loader.load_dataset("synthetic")

# Create splits
splitter = DatasetSplitter()
splits = splitter.create_splits(
    dataset,
    train_ratio=0.6,
    val_ratio=0.2,
    test_ratio=0.2,
    stratify=True  # Maintains label balance
)

print(f"Train: {len(splits['train'])} samples")
print(f"Val: {len(splits['val'])} samples")
print(f"Test: {len(splits['test'])} samples")

# Save splits
splitter.save_splits(splits)
```

## File Formats

### Test Case JSON Example

```json
{
  "id": "benign_001",
  "user_query": "Create a new directory called 'projects' in my home folder",
  "tools": [
    {
      "name": "CreateDirectory",
      "description": "Creates a new directory at the specified path",
      "parameters": {
        "path": {
          "type": "string",
          "description": "The directory path to create"
        }
      },
      "server": "FileSystemServer"
    }
  ],
  "expected_invocation": {
    "tool_name": "CreateDirectory",
    "arguments": {
      "path": "/home/user/projects"
    }
  },
  "label": "benign",
  "attack_type": "none",
  "metadata": {
    "domain": "filesystem",
    "complexity": "simple",
    "num_tools": 1
  }
}
```

## Git Integration

A `.gitignore` file is automatically created in the data directory with sensible defaults:

- Ignores large cache files (*.pt, *.pth, *.npy)
- Ignores generated visualizations
- Keeps directory structure
- Ignores MCPTox data (potential licensing issues)

## Testing

Run the utilities demo to ensure everything works:

```bash
python3 data_utils.py
```

Expected output:
```
==============================================================
MINDGUARD Data Utilities Demo
==============================================================

1. Loading example test case...
   Loaded: benign_001
   Query: Create a new directory called 'projects' in my home folder
   Label: benign
   Tools: 2

2. Validating test case...
   [OK] Test case is valid

3. Demonstrating cache functionality...
   Cached and loaded output: True

==============================================================
Demo complete!
==============================================================
```

## Troubleshooting

### Issue: Permission denied when running setup script
```bash
chmod +x setup_data_infrastructure.sh
```

### Issue: Python module not found
Ensure you're in the correct directory with both `.py` files:
```bash
ls -la *.py
```

### Issue: Directory already exists
The script is idempotent and safe to run multiple times. Existing files won't be overwritten.

### Issue: Schema validation fails
Check that your test case includes all required fields:
- id, user_query, tools, expected_invocation, label

## Next Steps

After completing this deliverable, you can proceed to:

1. **Phase 2, Task 2.1**: MCP Context Simulator
2. **Phase 2, Task 2.2**: Tool Poisoning Attack Generator
3. **Phase 2, Task 2.3**: Benign Dataset Creation

The infrastructure is now ready to receive generated data!

## Maintenance

### Adding New Schemas

1. Create a new JSON schema in `data/schemas/`
2. Update `DataValidator` class to include new validation logic

### Extending Test Case Structure

1. Update the `TestCase` dataclass in `data_utils.py`
2. Update the schema in `data/schemas/test_case_schema.json`
3. Regenerate example data

### Cleaning Cache

```python
from data_utils import CacheManager

cache = CacheManager()
cache.clear_cache("all")  # Clear everything
cache.clear_cache("attention")  # Clear only attention matrices
cache.clear_cache("output")  # Clear only outputs
```

## Success Criteria

- [x] Complete directory structure created
- [x] JSON schemas for all data types defined
- [x] Data classes with type hints implemented
- [x] Loading and saving utilities functional
- [x] Validation system working
- [x] Caching system implemented
- [x] Dataset splitting capability added
- [x] Example data files created
- [x] Documentation in every directory
- [x] Git integration configured

## Deliverable Checklist

- [x] Data directory structure (8+ subdirectories)
- [x] Dataset loading utilities
- [x] Synthetic test data generator framework
- [x] Data schemas for contexts, tools, and attacks
- [x] Data validation functions
- [x] Caching system for model outputs
- [x] Train/val/test split functionality
- [x] Example data files (2+)
- [x] Configuration management
- [x] Complete documentation

**Status**: [COMPLETE]

---

**Created**: [Date]
**Phase**: 1.3 - Data Infrastructure
**Next**: Phase 2.1 - MCP Context Simulator
