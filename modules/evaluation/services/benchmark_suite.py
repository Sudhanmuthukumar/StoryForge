import json
from pathlib import Path
from typing import List, Dict, Any

class BenchmarkSuite:
    """Manages curated prompts for evaluating Model Quality."""
    
    def __init__(self, filepath: str = "dataset_lab/benchmarks/benchmark_prompts.json"):
        self.filepath = Path(filepath)
        self.prompts = []
        self._load_prompts()
        
    def _load_prompts(self):
        if self.filepath.exists():
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.prompts = json.load(f)
                
    def get_all_benchmarks(self) -> List[Dict[str, Any]]:
        return self.prompts
        
    def get_benchmark_by_category(self, category: str) -> Dict[str, Any]:
        for b in self.prompts:
            if b.get("category") == category:
                return b
        return {}
