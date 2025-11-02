# Logging Framework Architecture

## Logging Strategy

MindGuard uses Python's `logging` module with structured logging for:
1. **Debugging**: Detailed step-by-step processing
2. **Monitoring**: Performance metrics and detection results
3. **Error Tracking**: Exceptions and warnings
4. **Audit Trail**: Detection decisions and attributions

## Log Levels

```
DEBUG   → Detailed processing steps (vertex extraction, TAE calculations)
INFO    → High-level operations (DDG built, detection completed)
WARNING → Non-critical issues (missing cache, fallback behavior)
ERROR   → Critical failures (model loading, parsing errors)
CRITICAL→ System failures (unrecoverable errors)
```

## Logger Hierarchy

```
mindguard (root)
  │
  ├──► mindguard.core
  │      ├──► mindguard.core.context_parser
  │      ├──► mindguard.core.ddg_builder
  │      ├──► mindguard.core.defender
  │      └──► mindguard.core.llm_wrapper
  │
  ├──► mindguard.attacks
  │      ├──► mindguard.attacks.attack_generator
  │      └──► mindguard.attacks.mcp_simulator
  │
  ├──► mindguard.visualization
  │      ├──► mindguard.visualization.ddg_viz
  │      ├──► mindguard.visualization.attention_viz
  │      └──► mindguard.visualization.metrics_viz
  │
  └──► mindguard.utils
         ├──► mindguard.utils.data_loader
         ├──► mindguard.utils.metrics
         └──► mindguard.utils.config
```

## Log Configuration

### Configuration File: `configs/logging_config.yaml`

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'
  
  detailed:
    format: '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'
  
  json:
    format: json
    # For structured logging (optional)

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/mindguard.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/mindguard_errors.log
    maxBytes: 10485760
    backupCount: 5

loggers:
  mindguard.core:
    level: DEBUG
    handlers: [console, file]
    propagate: false
  
  mindguard.attacks:
    level: INFO
    handlers: [console, file]
    propagate: false
  
  mindguard.visualization:
    level: INFO
    handlers: [console]
    propagate: false

root:
  level: INFO
  handlers: [console, file, error_file]
```

## Logging Usage Patterns

### Context Parser Logging
```python
import logging

logger = logging.getLogger('mindguard.core.context_parser')

def parse_context(context, output, tools):
    logger.debug(f"Parsing context: {len(context)} chars")
    logger.debug(f"Available tools: {[t.name for t in tools]}")
    
    try:
        vertices = extract_vertices(context, output, tools)
        logger.info(f"Extracted {len(vertices)} vertices")
        return vertices
    except Exception as e:
        logger.error(f"Context parsing failed: {e}", exc_info=True)
        raise
```

### DDG Builder Logging
```python
logger = logging.getLogger('mindguard.core.ddg_builder')

def build_ddg(attention, vertices):
    logger.debug(f"Building DDG from {len(vertices)} vertices")
    logger.debug(f"Attention shape: {attention.shape}")
    
    combined = combine_layers(attention)
    logger.debug("Layer aggregation completed")
    
    filtered = filter_sinks(combined)
    logger.debug(f"Sink filter removed {count_sinks(filtered)} tokens")
    
    ddg = create_graph(filtered, vertices)
    logger.info(f"DDG constructed: {len(ddg.vertices)} vertices, {len(ddg.edges)} edges")
    return ddg
```

### Defender Logging
```python
logger = logging.getLogger('mindguard.core.defender')

def detect_poisoning(ddg, threshold=0.5):
    logger.info(f"Starting detection with threshold={threshold}")
    
    results = []
    for tool in ddg.get_uninvoked_tools():
        air_control = compute_air(ddg, tool, 'invoked_tool_name')
        air_data = compute_air(ddg, tool, 'invoked_params')
        
        logger.debug(f"Tool {tool}: AIR_control={air_control:.3f}, AIR_data={air_data:.3f}")
        
        if air_control > threshold or air_data > threshold:
            logger.warning(f"POISONING DETECTED: Source={tool}, AIR_control={air_control:.3f}")
            return {
                'poisoned': True,
                'source': tool,
                'air_control': air_control,
                'air_data': air_data
            }
    
    logger.info("No poisoning detected")
    return {'poisoned': False}
```

## Log Files Structure

```
logs/
├── mindguard.log           # All logs (DEBUG and above)
├── mindguard_errors.log   # Errors only
└── mindguard_detections.json  # Detection results (structured)
```

## Structured Logging for Detections

```python
import json
import logging

def log_detection_result(result, test_case_id, metadata=None):
    """Log detection result in structured JSON format"""
    detection_log = {
        'timestamp': datetime.now().isoformat(),
        'test_case_id': test_case_id,
        'poisoned': result['poisoned'],
        'source': result.get('source'),
        'air_control': result.get('air_control'),
        'air_data': result.get('air_data'),
        'metadata': metadata or {}
    }
    
    logger.info(f"DETECTION: {json.dumps(detection_log)}")
    
    # Also write to dedicated detection log file
    with open('logs/mindguard_detections.json', 'a') as f:
        json.dump(detection_log, f)
        f.write('\n')
```

## Performance Logging

```python
import time
import logging

logger = logging.getLogger('mindguard.core')

def log_performance(operation, duration, metadata=None):
    """Log performance metrics"""
    perf_log = {
        'operation': operation,
        'duration_ms': duration * 1000,
        'metadata': metadata or {}
    }
    logger.debug(f"PERFORMANCE: {json.dumps(perf_log)}")
```

## Log Rotation

- Max file size: 10MB per log file
- Backup count: 5 files
- Automatic rotation when size limit reached

## Environment-based Configuration

```python
# Set log level via environment variable
LOG_LEVEL = os.getenv('MINDGUARD_LOG_LEVEL', 'INFO')

# Enable debug mode
if os.getenv('MINDGUARD_DEBUG', 'false').lower() == 'true':
    logging.getLogger('mindguard').setLevel(logging.DEBUG)
```

