"""
Data Management Utilities for MINDGUARD
Provides loading, validation, and manipulation functions for datasets
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import pickle


@dataclass
class Tool:
    """Represents a tool in the MCP context"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server: str = "UnknownServer"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Tool':
        return cls(**data)


@dataclass
class ToolInvocation:
    """Represents an expected or actual tool invocation"""
    tool_name: str
    arguments: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ToolInvocation':
        return cls(**data)


@dataclass
class TestCase:
    """Represents a complete test case"""
    id: str
    user_query: str
    tools: List[Tool]
    expected_invocation: ToolInvocation
    label: str  # "benign" or "poisoned"
    attack_type: str = "none"  # "none", "A1_explicit_hijacking", "A2_parameter_manipulation"
    poisoned_tool_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['tools'] = [tool.to_dict() for tool in self.tools]
        data['expected_invocation'] = self.expected_invocation.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestCase':
        tools = [Tool.from_dict(t) for t in data['tools']]
        expected_invocation = ToolInvocation.from_dict(data['expected_invocation'])
        
        return cls(
            id=data['id'],
            user_query=data['user_query'],
            tools=tools,
            expected_invocation=expected_invocation,
            label=data['label'],
            attack_type=data.get('attack_type', 'none'),
            poisoned_tool_id=data.get('poisoned_tool_id'),
            metadata=data.get('metadata', {})
        )
    
    def is_poisoned(self) -> bool:
        return self.label == "poisoned"
    
    def get_poisoned_tool(self) -> Optional[Tool]:
        """Returns the poisoned tool if it exists"""
        if not self.is_poisoned() or not self.poisoned_tool_id:
            return None
        
        for tool in self.tools:
            if tool.name == self.poisoned_tool_id:
                return tool
        return None


class DataLoader:
    """Handles loading and saving of test cases"""
    
    def __init__(self, data_root: str = "./data"):
        self.data_root = Path(data_root)
    
    def load_test_case(self, filepath: Path) -> TestCase:
        """Load a single test case from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return TestCase.from_dict(data)
    
    def save_test_case(self, test_case: TestCase, filepath: Path):
        """Save a test case to JSON file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(test_case.to_dict(), f, indent=2)
    
    def load_dataset(self, dataset_type: str = "synthetic") -> List[TestCase]:
        """
        Load all test cases from a dataset
        
        Args:
            dataset_type: "synthetic", "real_world", or "mcptox"
        """
        dataset_dir = self.data_root / dataset_type
        test_cases = []
        
        # Load from all subdirectories
        for json_file in dataset_dir.rglob("*.json"):
            # Skip schema and config files
            if "schema" in str(json_file) or "config" in str(json_file):
                continue
            
            try:
                test_case = self.load_test_case(json_file)
                test_cases.append(test_case)
            except Exception as e:
                print(f"Warning: Failed to load {json_file}: {e}")
        
        return test_cases
    
    def load_split(self, split: str) -> List[TestCase]:
        """
        Load a specific data split
        
        Args:
            split: "train", "val", or "test"
        """
        split_dir = self.data_root / "processed" / split
        test_cases = []
        
        for json_file in split_dir.glob("*.json"):
            try:
                test_case = self.load_test_case(json_file)
                test_cases.append(test_case)
            except Exception as e:
                print(f"Warning: Failed to load {json_file}: {e}")
        
        return test_cases
    
    def get_statistics(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Calculate statistics for a list of test cases"""
        
        total = len(test_cases)
        benign = sum(1 for tc in test_cases if tc.label == "benign")
        poisoned = sum(1 for tc in test_cases if tc.label == "poisoned")
        
        attack_types: Dict[str, int] = {}
        domains: Dict[str, int] = {}
        
        for tc in test_cases:
            # Count attack types
            attack_type = tc.attack_type
            attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
            
            # Count domains
            domain = tc.metadata.get('domain', 'unknown')
            domains[domain] = domains.get(domain, 0) + 1
        
        return {
            'total': total,
            'benign': benign,
            'poisoned': poisoned,
            'balance': f"{benign}/{poisoned}" if poisoned > 0 else "N/A",
            'attack_types': attack_types,
            'domains': domains
        }


class DataValidator:
    """Validates test cases against schemas"""
    
    def __init__(self, schema_dir: Path = None):
        if schema_dir is None:
            schema_dir = Path("./data/schemas")
        self.schema_dir = schema_dir
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all schemas from schema directory"""
        self.schemas = {}
        
        if self.schema_dir.exists():
            for schema_file in self.schema_dir.glob("*.json"):
                with open(schema_file, 'r') as f:
                    schema_name = schema_file.stem
                    self.schemas[schema_name] = json.load(f)
    
    def validate_tool(self, tool: Tool) -> Tuple[bool, List[str]]:
        """Validate a tool against schema"""
        errors = []
        
        if not tool.name:
            errors.append("Tool name is required")
        
        if not tool.description:
            errors.append("Tool description is required")
        
        if not isinstance(tool.parameters, dict):
            errors.append("Tool parameters must be a dictionary")
        
        return len(errors) == 0, errors
    
    def validate_test_case(self, test_case: TestCase) -> Tuple[bool, List[str]]:
        """Validate a complete test case"""
        errors = []
        
        # Check required fields
        if not test_case.id:
            errors.append("Test case ID is required")
        
        if not test_case.user_query:
            errors.append("User query is required")
        
        if not test_case.tools:
            errors.append("At least one tool is required")
        
        if test_case.label not in ["benign", "poisoned"]:
            errors.append(f"Invalid label: {test_case.label}")
        
        # Validate each tool
        for i, tool in enumerate(test_case.tools):
            valid, tool_errors = self.validate_tool(tool)
            if not valid:
                errors.extend([f"Tool {i}: {e}" for e in tool_errors])
        
        # Validate poisoned-specific fields
        if test_case.is_poisoned():
            if test_case.attack_type not in ["A1_explicit_hijacking", "A2_parameter_manipulation"]:
                errors.append(f"Invalid attack type: {test_case.attack_type}")
            
            if not test_case.poisoned_tool_id:
                errors.append("Poisoned test case must specify poisoned_tool_id")
            else:
                # Check if poisoned tool exists
                tool_names = [t.name for t in test_case.tools]
                if test_case.poisoned_tool_id not in tool_names:
                    errors.append(f"Poisoned tool '{test_case.poisoned_tool_id}' not found in tools")
        
        return len(errors) == 0, errors


class CacheManager:
    """Manages caching of model outputs and attention matrices"""
    
    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            cache_dir = Path("./data/cache")
        self.cache_dir = cache_dir
        self.attention_dir = cache_dir / "attention_matrices"
        self.output_dir = cache_dir / "model_outputs"
        
        # Create directories
        self.attention_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, test_case_id: str, model_name: str) -> str:
        """Generate unique cache key"""
        key_string = f"{test_case_id}_{model_name}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def save_attention(self, test_case_id: str, model_name: str, attention_data: Any):
        """Save attention matrix to cache"""
        cache_key = self._get_cache_key(test_case_id, model_name)
        filepath = self.attention_dir / f"{cache_key}.pkl"
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'test_case_id': test_case_id,
                'model_name': model_name,
                'attention_data': attention_data,
                'timestamp': datetime.now().isoformat()
            }, f)
    
    def load_attention(self, test_case_id: str, model_name: str) -> Optional[Any]:
        """Load attention matrix from cache"""
        cache_key = self._get_cache_key(test_case_id, model_name)
        filepath = self.attention_dir / f"{cache_key}.pkl"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            return data['attention_data']
    
    def save_output(self, test_case_id: str, model_name: str, output: Dict[str, Any]):
        """Save model output to cache"""
        cache_key = self._get_cache_key(test_case_id, model_name)
        filepath = self.output_dir / f"{cache_key}.json"
        
        output_data = {
            'test_case_id': test_case_id,
            'model_name': model_name,
            'output': output,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
    
    def load_output(self, test_case_id: str, model_name: str) -> Optional[Any]:
        """Load model output from cache"""
        cache_key = self._get_cache_key(test_case_id, model_name)
        filepath = self.output_dir / f"{cache_key}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get('output')
    
    def clear_cache(self, cache_type: str = "all"):
        """Clear cache files"""
        if cache_type in ["all", "attention"]:
            for file in self.attention_dir.glob("*.pkl"):
                file.unlink()
            print(f"Cleared attention cache")
        
        if cache_type in ["all", "output"]:
            for file in self.output_dir.glob("*.json"):
                file.unlink()
            print(f"Cleared output cache")


class DatasetSplitter:
    """Creates train/val/test splits from datasets"""
    
    def __init__(self, data_root: Path = None):
        if data_root is None:
            data_root = Path("./data")
        self.data_root = data_root
        self.loader = DataLoader(data_root=str(data_root))
    
    def create_splits(
        self, 
        test_cases: List[TestCase],
        train_ratio: float = 0.6,
        val_ratio: float = 0.2,
        test_ratio: float = 0.2,
        stratify: bool = True
    ) -> Dict[str, List[TestCase]]:
        """
        Split test cases into train/val/test sets
        
        Args:
            test_cases: List of test cases to split
            train_ratio: Proportion for training
            val_ratio: Proportion for validation
            test_ratio: Proportion for testing
            stratify: Whether to maintain label balance in splits
        """
        import random
        
        # Validate ratios
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Ratios must sum to 1"
        
        if stratify:
            # Separate by label
            benign = [tc for tc in test_cases if tc.label == "benign"]
            poisoned = [tc for tc in test_cases if tc.label == "poisoned"]
            
            # Shuffle
            random.shuffle(benign)
            random.shuffle(poisoned)
            
            # Split each group
            def split_group(group):
                n = len(group)
                train_end = int(n * train_ratio)
                val_end = train_end + int(n * val_ratio)
                
                return {
                    'train': group[:train_end],
                    'val': group[train_end:val_end],
                    'test': group[val_end:]
                }
            
            benign_splits = split_group(benign)
            poisoned_splits = split_group(poisoned)
            
            # Combine
            splits = {
                'train': benign_splits['train'] + poisoned_splits['train'],
                'val': benign_splits['val'] + poisoned_splits['val'],
                'test': benign_splits['test'] + poisoned_splits['test']
            }
            
            # Shuffle combined splits
            for split_name in splits:
                random.shuffle(splits[split_name])
        
        else:
            # Simple random split
            random.shuffle(test_cases)
            n = len(test_cases)
            train_end = int(n * train_ratio)
            val_end = train_end + int(n * val_ratio)
            
            splits = {
                'train': test_cases[:train_end],
                'val': test_cases[train_end:val_end],
                'test': test_cases[val_end:]
            }
        
        return splits
    
    def save_splits(self, splits: Dict[str, List[TestCase]]):
        """Save splits to processed directory"""
        for split_name, test_cases in splits.items():
            split_dir = self.data_root / "processed" / split_name
            split_dir.mkdir(parents=True, exist_ok=True)
            
            for tc in test_cases:
                filepath = split_dir / f"{tc.id}.json"
                self.loader.save_test_case(tc, filepath)
            
            print(f"Saved {len(test_cases)} test cases to {split_dir}")


# Example usage and testing
def main():
    """Example usage of data utilities"""
    
    print("="*60)
    print("MINDGUARD Data Utilities Demo")
    print("="*60)
    
    # Initialize components
    loader = DataLoader()
    validator = DataValidator()
    cache_manager = CacheManager()
    
    # Load example data
    print("\n1. Loading example test case...")
    example_file = Path("./data/examples/benign_example.json")
    if example_file.exists():
        test_case = loader.load_test_case(example_file)
        print(f"   Loaded: {test_case.id}")
        print(f"   Query: {test_case.user_query}")
        print(f"   Label: {test_case.label}")
        print(f"   Tools: {len(test_case.tools)}")
        
        # Validate
        print("\n2. Validating test case...")
        valid, errors = validator.validate_test_case(test_case)
        if valid:
            print("   ✓ Test case is valid")
        else:
            print("   ✗ Validation errors:")
            for error in errors:
                print(f"     - {error}")
    
    # Demonstrate caching
    print("\n3. Demonstrating cache functionality...")
    test_output = {
        'tool_name': 'CreateDirectory',
        'arguments': {'path': '/home/user/projects'}
    }
    cache_manager.save_output("test_001", "qwen-7b", test_output)
    loaded = cache_manager.load_output("test_001", "qwen-7b")
    print(f"   Cached and loaded output: {loaded is not None}")
    
    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60)


if __name__ == "__main__":
    main()
