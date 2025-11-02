# Synthetic Dataset

Artificially generated test cases for controlled experiments.

## Subdirectories:
- `benign/`: Legitimate tool calling scenarios (50 samples)
- `poisoned/A1_explicit_hijacking/`: Explicit invocation hijacking attacks (25 samples)
- `poisoned/A2_parameter_manipulation/`: Parameter manipulation attacks (25 samples)
- `raw/`: Raw generated data before processing

## File Format:
Each test case is stored as JSON following the test_case_schema.
