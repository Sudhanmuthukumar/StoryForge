import re
import json
from pathlib import Path
from typing import List, Dict, Any

class ChapterSplitter:
    """Splits raw text into chapter segments with strict Series/Book/Volume/Part/Chapter hierarchy."""
    
    def __init__(self, output_dir: str = "dataset_lab/chapters"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def split(self, file_path: str, title: str, raw_text: str) -> List[Dict[str, Any]]:
        # Regex to catch hierarchies. 
        # Groups: header_type, header_value
        pattern = re.compile(
            r'(?:^|\n)(?P<header_type>Series|Book|Volume|Part|Chapter|Prologue|Epilogue)\s+(?P<header_val>[A-Za-z0-9\-\.\:\s]+?)(?:\n|$)', 
            re.IGNORECASE
        )
        
        matches = list(pattern.finditer(raw_text))
        chapters = []
        
        # State tracking
        state = {
            "series": "",
            "book": title,
            "volume": "",
            "part": "",
            "chapter": ""
        }
        
        if not matches:
            state["chapter"] = "Entire Document"
            chapters.append(self._create_chapter_json(file_path, state, 1, raw_text.strip()))
            return chapters

        # Process frontmatter
        frontmatter = raw_text[:matches[0].start()].strip()
        if frontmatter and len(frontmatter.split()) > 50:
            state["chapter"] = "Frontmatter"
            chapters.append(self._create_chapter_json(file_path, state, 0, frontmatter))
            
        chapter_index = 1
        
        for i, match in enumerate(matches):
            h_type = match.group("header_type").strip().lower()
            h_val = match.group("header_val").strip()
            full_header = f"{h_type.title()} {h_val}"
            
            # Update state based on type (never overwrite parent hierarchy)
            if h_type == "series":
                state["series"] = h_val
            elif h_type == "book":
                state["book"] = h_val
            elif h_type == "volume":
                state["volume"] = h_val
            elif h_type == "part":
                state["part"] = h_val
            else:
                state["chapter"] = full_header
                
            start_pos = match.end()
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(raw_text)
            
            segment_text = raw_text[start_pos:end_pos].strip()
            
            # If there's meaningful text, save it as a chapter block
            if segment_text and len(segment_text.split()) > 20:
                # If we haven't hit a chapter yet but have text (e.g., Book 1 intro)
                if h_type != "chapter" and h_type != "prologue" and h_type != "epilogue":
                    temp_chap_name = f"Intro to {full_header}"
                    old_chap = state["chapter"]
                    state["chapter"] = temp_chap_name
                    chapters.append(self._create_chapter_json(file_path, state, chapter_index, segment_text))
                    state["chapter"] = old_chap
                else:
                    chapters.append(self._create_chapter_json(file_path, state, chapter_index, segment_text))
                chapter_index += 1
                
        return chapters
        
    def _create_chapter_json(self, source_file: str, state: Dict[str, str], chapter_index: int, text: str) -> Dict[str, Any]:
        return {
            "source_file": Path(source_file).name,
            "series": state["series"],
            "book": state["book"],
            "volume": state["volume"],
            "part": state["part"],
            "chapter": state["chapter"],
            "chapter_index": chapter_index,
            "page_start": 0,
            "page_end": 0,
            "word_count": len(text.split()),
            "text": text
        }
        
    def save_chapter(self, chapter_data: Dict[str, Any]) -> str:
        book_safe = chapter_data["book"].replace(" ", "_").replace("/", "_").replace("\\", "_")
        if not book_safe:
            book_safe = "Unknown_Book"
            
        idx = chapter_data["chapter_index"]
        filename = f"{book_safe}_chap_{idx:03d}.json"
        out_path = self.output_dir / filename
        
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=4)
            
        return str(out_path)
