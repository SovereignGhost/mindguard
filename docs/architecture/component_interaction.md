# Component Interaction Diagrams

## Class Diagram (Simplified UML)

```
┌─────────────────────────────────────────────────────────────┐
│                     LLMWrapper                              │
├─────────────────────────────────────────────────────────────┤
│ - model: AutoModelForCausalLM                              │
│ - tokenizer: AutoTokenizer                                 │
│ - cache: CacheManager                                      │
├─────────────────────────────────────────────────────────────┤
│ + load_model(name: str) -> Tuple[Model, Tokenizer]         │
│ + infer(context: str) -> Dict[str, Any]                    │
│ + extract_attention() -> Tensor                            │
│ + tokenize(text: str) -> List[int]                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ uses
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    ContextParser                            │
├─────────────────────────────────────────────────────────────┤
│ - token_to_text: Dict[int, str]                           │
│ - context_str: str                                          │
│ - output_str: str                                           │
├─────────────────────────────────────────────────────────────┤
│ + parse_context(context, output, tools) -> Dict[str, List] │
│ + locate_user_query_tokens() -> List[int]                  │
│ + locate_tool_tokens(tool) -> List[int]                   │
│ + locate_invoked_name() -> List[int]                      │
│ + locate_invoked_params() -> List[int]                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ produces
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      DDGBuilder                              │
├─────────────────────────────────────────────────────────────┤
│ - attention_layers: Tensor                                  │
│ - vertices: Dict[str, List[int]]                            │
│ - config: Dict[str, Any]                                    │
├─────────────────────────────────────────────────────────────┤
│ + build_ddg(attention, vertices) -> DDG                     │
│ + combine_layers(attention) -> Tensor                       │
│ + filter_sinks(attention, k, epsilon) -> Tensor           │
│ + compute_tae(submatrix) -> float                           │
│ + create_graph(edges) -> Graph                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ produces
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   AnomalyAwareDefender                       │
├─────────────────────────────────────────────────────────────┤
│ - ddg: Graph                                                 │
│ - threshold: float                                           │
│ - config: Dict[str, Any]                                    │
├─────────────────────────────────────────────────────────────┤
│ + detect_poisoning(ddg) -> Dict[str, Any]                  │
│ + compute_air(source, target) -> float                     │
│ + attribute_source(ddg) -> str                             │
│ + separate_flows(ddg) -> Tuple[float, float]               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ uses
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      DDG (Graph)                            │
├─────────────────────────────────────────────────────────────┤
│ - vertices: Set[str]                                        │
│ - edges: Dict[(str, str), float]                           │
│ - metadata: Dict[str, Any]                                  │
├─────────────────────────────────────────────────────────────┤
│ + get_weight(source, target) -> float                      │
│ + get_uninvoked_tools() -> List[str]                       │
│ + get_vertex_tokens(vertex) -> List[int]                   │
│ + serialize() -> Dict[str, Any]                            │
└─────────────────────────────────────────────────────────────┘
```

## Sequence Diagram: Detection Pipeline

```
User/MCP    LLMWrapper    ContextParser    DDGBuilder    Defender
   │             │              │              │             │
   │──query─────▶│              │              │             │
   │             │              │              │             │
   │             │──infer──────▶│              │             │
   │             │              │              │             │
   │             │◀─attention───│              │             │
   │             │   + output   │              │             │
   │             │              │              │             │
   │             │────parse────▶│              │             │
   │             │  (context,   │              │             │
   │             │   output)    │              │             │
   │             │              │              │             │
   │             │◀──vertices───│              │             │
   │             │              │              │             │
   │             │──build_ddg───┼─────────────▶│             │
   │             │  (attention, │              │             │
   │             │   vertices)  │              │             │
   │             │              │              │             │
   │             │              │◀──combine────│             │
   │             │              │   layers     │             │
   │             │              │              │             │
   │             │              │◀──filter─────│             │
   │             │              │   sinks      │             │
   │             │              │              │             │
   │             │              │◀──compute───│             │
   │             │              │   TAE       │             │
   │             │              │              │             │
   │             │◀──ddg────────│              │             │
   │             │              │              │             │
   │             │──detect──────┼──────────────┼────────────▶│
   │             │  (ddg)       │              │             │
   │             │              │              │             │
   │             │              │              │◀─compute_air│
   │             │              │              │             │
   │             │              │              │◀─compare────│
   │             │              │              │  threshold  │
   │             │              │              │             │
   │             │◀──verdict────┼──────────────┼─────────────│
   │             │              │              │             │
   │◀─result─────│              │              │             │
```

## Module Dependencies

```
┌─────────────────┐
│   Main Entry    │
│   (demo/app.py) │
└────────┬────────┘
         │
         ├──────────────┬──────────────┬─────────────┐
         │              │              │             │
         ▼              ▼              ▼             ▼
┌──────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────────┐
│ LLMWrapper  │  │ContextParser│  │DDGBuilder│  │   Defender   │
└──────────────┘  └─────────────┘  └──────────┘  └──────────────┘
         │              │              │             │
         │              │              │             │
         └──────────────┼──────────────┼─────────────┘
                        │              │
                        ▼              ▼
                  ┌─────────────┐  ┌──────────┐
                  │   Utils     │  │  Config  │
                  │             │  │          │
                  │ - data_loader│  │ - YAML   │
                  │ - metrics   │  │ - env    │
                  │ - cache     │  │          │
                  └─────────────┘  └──────────┘
```

## Data Structure Relationships

```
TestCase
  │
  ├──► Tool (multiple)
  │      │
  │      └──► ToolMetadata
  │
  └──► ToolInvocation
         │
         ├──► tool_name: str
         └──► arguments: Dict[str, Any]

         │
         ▼

DDG Vertices
  │
  ├──► v_u: user_query (tokens)
  ├──► v_t: tool_descriptions (multiple, tokens)
  ├──► v_c_t: invoked_tool_name (tokens)
  └──► v_c_p: invoked_params (tokens)

         │
         ▼

DDG Graph
  │
  ├──► Vertices: Set[str]
  └──► Edges: Dict[(source, target), weight]
         │
         │ weight = TAE(source → target)
         │
         ▼

Detection Result
  │
  ├──► poisoned: bool
  ├──► source: str (tool name if poisoned)
  ├──► air_control: float
  ├──► air_data: float
  └──► metadata: Dict[str, Any]
```

