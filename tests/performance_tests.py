import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.memory_extractor import MemoryExtractor
from services.relationship_extractor import RelationshipExtractor
from services.character_profiler import CharacterProfiler
from services.story_analyzer import StoryAnalyzer
from services.consistency_engine import ConsistencyEngine

def run_performance():
    # 10,000 words
    content = "Arjun walked into the grand hall. He saw many people. " * 2000
    
    mem = MemoryExtractor()
    rel = RelationshipExtractor()
    char = CharacterProfiler()
    ana = StoryAnalyzer()
    con = ConsistencyEngine()

    timings = {}

    t0 = time.time()
    m_dict = mem.extract(content)
    timings["memory_engine_ms"] = int((time.time() - t0) * 1000)

    t0 = time.time()
    m_dict["relationships"] = rel.extract_relationships(content, m_dict)
    timings["relationship_engine_ms"] = int((time.time() - t0) * 1000)

    t0 = time.time()
    char.profile_all_characters(content, m_dict)
    timings["character_engine_ms"] = int((time.time() - t0) * 1000)

    t0 = time.time()
    a_dict = ana.analyze_story(m_dict)
    timings["analysis_engine_ms"] = int((time.time() - t0) * 1000)

    t0 = time.time()
    c_dict = con.check_consistency(m_dict, a_dict)
    timings["consistency_engine_ms"] = int((time.time() - t0) * 1000)
    
    # Generate Benchmark Report
    report_path = Path("c:/StoryForge AI/reports/benchmark_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(timings, f, indent=2)
        
    print(json.dumps(timings, indent=2))

if __name__ == "__main__":
    run_performance()
