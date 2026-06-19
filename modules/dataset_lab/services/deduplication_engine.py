import json
import hashlib
import math
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List

class DeduplicationEngine:
    """Detects duplicate and near-duplicate training examples."""
    
    def __init__(self, input_dir: str = "dataset_lab/training/pilot"):
        self.input_dir = Path(input_dir)
        self.report_path = self.input_dir.parent / "logs" / "duplicate_report.json"
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _get_tokens(self, text: str) -> List[str]:
        return text.lower().replace(".", "").replace(",", "").split()
        
    def _cosine_sim(self, text1: str, text2: str) -> float:
        vec1 = Counter(self._get_tokens(text1))
        vec2 = Counter(self._get_tokens(text2))
        
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        
        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def _ngram_sim(self, text1: str, text2: str, n=3) -> float:
        t1 = self._get_tokens(text1)
        t2 = self._get_tokens(text2)
        if len(t1) < n or len(t2) < n:
            return self._cosine_sim(text1, text2)
            
        ngrams1 = set([" ".join(t1[i:i+n]) for i in range(len(t1)-n+1)])
        ngrams2 = set([" ".join(t2[i:i+n]) for i in range(len(t2)-n+1)])
        
        if not ngrams1 or not ngrams2:
            return 0.0
            
        overlap = ngrams1 & ngrams2
        return len(overlap) / min(len(ngrams1), len(ngrams2))

    def detect_duplicates(self) -> List[Dict[str, Any]]:
        if not self.input_dir.exists():
            return []
            
        examples = []
        # Load all examples
        for file_path in self.input_dir.glob("*.jsonl"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        ex = json.loads(line)
                        ex["_file"] = file_path.name
                        unique_string = f"{ex.get('instruction', '')}_{ex.get('input', '')}_{ex.get('output', '')}"
                        ex["_id"] = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
                        examples.append(ex)
                    except Exception:
                        continue
                        
        report = []
        processed_hashes = {} # id -> ex
        
        for ex in examples:
            ex_id = ex["_id"]
            out_text = ex.get("output", "")
            
            # Exact Hash Check
            if ex_id in processed_hashes:
                report.append({
                    "example_id": ex_id,
                    "status": "DUPLICATE",
                    "reason": "Exact Hash Match",
                    "similar_to": processed_hashes[ex_id]["_id"]
                })
                continue
                
            # Similarity Checks against already processed
            status = "SAFE"
            reason = ""
            similar_to = ""
            
            for p_id, p_ex in processed_hashes.items():
                p_out = p_ex.get("output", "")
                
                cos_sim = self._cosine_sim(out_text, p_out)
                if cos_sim > 0.85:
                    status = "DUPLICATE" if cos_sim > 0.95 else "SIMILAR"
                    reason = f"Cosine Similarity ({cos_sim:.2f})"
                    similar_to = p_id
                    break
                    
                ngram = self._ngram_sim(out_text, p_out)
                if ngram > 0.6:
                    status = "DUPLICATE" if ngram > 0.8 else "SIMILAR"
                    reason = f"N-Gram Overlap ({ngram:.2f})"
                    similar_to = p_id
                    break
                    
            report.append({
                "example_id": ex_id,
                "status": status,
                "reason": reason,
                "similar_to": similar_to
            })
            
            if status == "SAFE":
                processed_hashes[ex_id] = ex
                
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
            
        return report
