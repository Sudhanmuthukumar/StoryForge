import os
import json
from pathlib import Path

class ValidationReporter:
    """Generates validation reports for Dataset Lab Chapter extraction."""
    
    def __init__(self, chapters_dir: str = "dataset_lab/chapters"):
        self.chapters_dir = Path(chapters_dir)
        
    def generate_reports(self) -> None:
        if not self.chapters_dir.exists():
            return
            
        all_chapters = []
        books_detected = set()
        files_processed = set()
        
        # Load all chapters
        for path in self.chapters_dir.glob("*.json"):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    all_chapters.append(data)
                    books_detected.add(data.get("book", ""))
                    files_processed.add(data.get("source_file", ""))
                except Exception:
                    continue
                    
        if not all_chapters:
            return
            
        # 1. Generate chapter_validation_report.json
        validation_data = []
        warnings = []
        errors = []
        
        largest_chap = None
        smallest_chap = None
        total_words = 0
        
        for chap in all_chapters:
            word_count = chap.get("word_count", 0)
            text = chap.get("text", "")
            first_200 = text[:200]
            last_200 = text[-200:] if len(text) > 200 else text
            
            validation_data.append({
                "book": chap.get("book"),
                "chapter": chap.get("chapter"),
                "word_count": word_count,
                "first_200_chars": first_200,
                "last_200_chars": last_200
            })
            
            if word_count < 100 and chap.get("chapter") != "Frontmatter":
                warnings.append(f"Chapter '{chap.get('chapter')}' in '{chap.get('book')}' is suspiciously short ({word_count} words).")
            if word_count > 15000:
                warnings.append(f"Chapter '{chap.get('chapter')}' in '{chap.get('book')}' is suspiciously long ({word_count} words). Check for missed splits.")
                
            if not chap.get("book") or not chap.get("chapter"):
                errors.append(f"Missing mandatory metadata in chapter index {chap.get('chapter_index')}.")
                
            total_words += word_count
            if not largest_chap or word_count > largest_chap["word_count"]:
                largest_chap = chap
            if not smallest_chap or word_count < smallest_chap["word_count"]:
                smallest_chap = chap
                
        val_json_path = self.chapters_dir.parent / "logs" / "chapter_validation_report.json"
        val_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(val_json_path, "w", encoding="utf-8") as f:
            json.dump(validation_data, f, indent=4)
            
        # 2. Generate dataset_validation_report.md
        avg_words = total_words // len(all_chapters)
        
        md_content = [
            "# Dataset Validation Report",
            "",
            "## Summary",
            f"- **Files Processed**: {len(files_processed)}",
            f"- **Books Detected**: {len(books_detected)}",
            f"- **Chapters Detected**: {len(all_chapters)}",
            f"- **Average Chapter Length**: {avg_words} words",
            "",
            "## Extremes",
            f"- **Largest Chapter**: {largest_chap.get('chapter', 'N/A')} ({largest_chap.get('word_count', 0)} words) - Book: {largest_chap.get('book', 'N/A')}",
            f"- **Smallest Chapter**: {smallest_chap.get('chapter', 'N/A')} ({smallest_chap.get('word_count', 0)} words) - Book: {smallest_chap.get('book', 'N/A')}",
            "",
            "## Metadata Accuracy",
            f"- **Metadata Errors**: {len(errors)}",
            "",
            "## Validation Warnings",
        ]
        
        if warnings:
            for w in warnings:
                md_content.append(f"- {w}")
        else:
            md_content.append("- No warnings detected.")
            
        if errors:
            md_content.append("")
            md_content.append("## Extraction Errors")
            for e in errors:
                md_content.append(f"- {e}")
                
        md_path = self.chapters_dir.parent / "logs" / "dataset_validation_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
            
if __name__ == "__main__":
    ValidationReporter().generate_reports()
