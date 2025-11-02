# Data Flow Documentation

## End-to-End Processing Flow

### Phase 1: Input Preparation
```
User Query + Tool Metadata
         │
         ▼
┌──────────────────────┐
│  MCP Context Builder │
│  (mcp_simulator.py)  │
└──────────┬───────────┘
           │
           ▼
   Formatted Context String
   (ready for LLM input)
```

### Phase 2: LLM Inference
```
Formatted Context
      │
      ▼
┌──────────────────────┐
│   LLM Wrapper       │
│   (llm_wrapper.py)   │
│                      │
│  - Tokenize         │
│  - Run inference    │
│  - Extract attention│
└──────────┬───────────┘
           │
           ▼
    ┌──────────────┐
    │ Token IDs    │
    │ Attention    │ ← Shape: [layers, heads, seq_len, seq_len]
    │ Output Text  │
    └──────────────┘
```

### Phase 3: Context Parsing
```
Token IDs + Output Text
         │
         ▼
┌──────────────────────┐
│  Context Parser      │
│  (context_parser.py) │
│                      │
│  Functions:          │
│  - locate_user_query │
│  - locate_tool_tokens│
│  - locate_invoked_   │
│    name/params       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Vertex Dictionary  │
│                      │
│  {                   │
│    'user_query':     │
│      [token_indices],│
│    'tools': [        │
│      {name: str,     │
│       tokens: [int]} │
│    ],                │
│    'invoked_tool_name'│
│      : [token_indices],│
│    'invoked_params': │
│      [token_indices] │
│  }                   │
└──────────┬───────────┘
```

### Phase 4: DDG Construction
```
Attention Matrices + Vertices
         │
         ▼
┌──────────────────────┐
│   DDG Builder        │
│   (ddg_builder.py)   │
│                      │
│  Step 1:            │
│  ┌────────────────┐ │
│  │ Gaussian-weight│ │
│  │ layer aggreg.  │ │
│  └────────────────┘ │
│         │            │
│         ▼            │
│  ┌────────────────┐ │
│  │ Sink Filter    │ │
│  │ (2-stage)      │ │
│  └────────────────┘ │
│         │            │
│         ▼            │
│  ┌────────────────┐ │
│  │ TAE Calculation│ │
│  │ (per edge)     │ │
│  └────────────────┘ │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   DDG Graph          │
│                      │
│  Graph Structure:   │
│  - Vertices: dict    │
│  - Edges: dict       │
│    {source → target: │
│     weight (float)}   │
└──────────┬───────────┘
```

### Phase 5: Anomaly Detection
```
DDG Graph
    │
    ▼
┌──────────────────────┐
│  Anomaly-aware       │
│  Defender          │
│  (defender.py)     │
│                     │
│  For each           │
│  uninvoked tool:    │
│  ┌────────────────┐ │
│  │ Compute AIR    │ │
│  │ (control flow) │ │
│  └────────────────┘ │
│  ┌────────────────┐ │
│  │ Compute AIR    │ │
│  │ (data flow)    │ │
│  └────────────────┘ │
│  ┌────────────────┐ │
│  │ Compare to     │ │
│  │ threshold      │ │
│  └────────────────┘ │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Detection Result   │
│                      │
│  {                   │
│    'poisoned': bool,  │
│    'source': str,     │ ← Tool name if poisoned
│    'air_control': float,│
│    'air_data': float,│
│    'threshold': float│
│  }                   │
└──────────────────────┘
```

## Data Transformations

### Input → Context Parser
```python
Input:
  - context: str = "User: {query}\nTools: {tool_descriptions}"
  - output: str = "invoke_tool(name='ReadFile', args={...})"
  - token_ids: List[int]
  - token_text: List[str]

Transform:
  - Map text spans to token indices
  - Identify boundaries between user query, tools, invocation

Output:
  - vertices: Dict[str, List[int]]
```

### Attention → DDG
```python
Input:
  - attention_layers: Tensor[layers, heads, seq_len, seq_len]
  - vertices: Dict[str, List[int]]

Transform:
  - Aggregate layers (Gaussian-weighted)
  - Filter sinks (2-stage)
  - Extract submatrices per vertex pair
  - Compute TAE: sum(attention_submatrix²)

Output:
  - ddg: Graph {
      vertices: Set[str],
      edges: Dict[(str, str), float]
    }
```

### DDG → Detection
```python
Input:
  - ddg: Graph with weighted edges
  - threshold: float = 0.5

Transform:
  - For each uninvoked tool t:
      air_control = w(t → invoked_name) / (w(user → invoked_name) + w(invoked → invoked_name))
      air_data = w(t → invoked_params) / (w(user → invoked_params) + w(invoked → invoked_params))
  - If max(air_control, air_data) > threshold → POISONED

Output:
  - verdict: Dict with detection result and attribution
```

## Caching Strategy

```
LLM Output + Attention
        │
        ▼
┌──────────────────────┐
│  Cache Manager       │
│  (data_utils.py)     │
│                      │
│  Key:                │
│  hash(test_case_id + │
│       model_name)    │
│                      │
│  Cache:              │
│  - Attention matrices│
│  - Model outputs     │
│  - DDG graphs        │
└──────────────────────┘
```

## Error Handling Flow

```
Any Module
    │
    ▼ (error occurs)
┌──────────────────────┐
│  Logging Framework   │
│  - Record error      │
│  - Context info      │
│  - Stack trace       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Error Handler       │
│  - Return safe       │
│    default           │
│  - Continue pipeline │
│  - Alert user        │
└──────────────────────┘
```

