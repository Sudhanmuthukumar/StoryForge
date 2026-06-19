from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QTextEdit, QPushButton, QHBoxLayout, QComboBox
from modules.knowledge_engine.services.knowledge_database import KnowledgeDatabase

class WriterWorkspaceView(QWidget):
    def __init__(self):
        super().__init__()
        self.db = KnowledgeDatabase()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("<b>Writer Workspace</b> - Powered by StoryForge Knowledge Engine")
        header.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        
        self._init_writer_tab()
        self._init_character_studio()
        self._init_scene_builder()
        self._init_worldbuilding_studio()
        self._init_story_analyzer()
        
        layout.addWidget(self.tabs)

    def _init_writer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        ctrl_layout = QHBoxLayout()
        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["Fantasy", "Sci-Fi", "Mystery", "Adventure"])
        ctrl_layout.addWidget(QLabel("Genre:"))
        ctrl_layout.addWidget(self.genre_combo)
        
        self.tone_combo = QComboBox()
        self.tone_combo.addItems(["Epic", "Grimdark", "Lighthearted", "Suspenseful"])
        ctrl_layout.addWidget(QLabel("Tone:"))
        ctrl_layout.addWidget(self.tone_combo)
        
        layout.addLayout(ctrl_layout)
        
        self.writer_text = QTextEdit()
        self.writer_text.setPlaceholderText("Write your story here... (Generative features pull from proven high-success narrative patterns)")
        layout.addWidget(self.writer_text)
        
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton("Generate Continuation (Ollama)")
        generate_btn.setStyleSheet("background-color: #2196F3; color: white;")
        btn_layout.addWidget(generate_btn)
        layout.addLayout(btn_layout)
        
        self.tabs.addTab(tab, "Writer")

    def _init_character_studio(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("<b>Character Patterns</b> (Highest Success Score First)"))
        
        self.char_display = QTextEdit()
        self.char_display.setReadOnly(True)
        
        # Load characters from DB
        chars = self.db.read_db("character_patterns.json")
        chars.sort(key=lambda x: x.get("success_score", 0), reverse=True)
        
        text = ""
        for c in chars:
            text += f"Archetype: {c.get('name')} (Score: {c.get('success_score')})\n{c.get('description')}\n\n"
            
        if not text:
            text = "No character patterns extracted yet. Run Dataset Lab on a book!"
            
        self.char_display.setText(text)
        layout.addWidget(self.char_display)
        self.tabs.addTab(tab, "Character Studio")

    def _init_scene_builder(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("<b>Scene Builder</b> - Select a proven Scene Pattern from the Knowledge Engine to scaffold your next chapter."))
        self.tabs.addTab(tab, "Scene Builder")

    def _init_worldbuilding_studio(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("<b>Worldbuilding Studio</b> - Design Magic Systems and Factions using extracted literature patterns."))
        self.tabs.addTab(tab, "Worldbuilding")

    def _init_story_analyzer(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("<b>Story Analyzer</b> - Paste your chapter below to compare its pacing and structure against our high-performing database models."))
        
        self.analyzer_input = QTextEdit()
        self.analyzer_input.setPlaceholderText("Paste your chapter here...")
        layout.addWidget(self.analyzer_input)
        
        analyze_btn = QPushButton("Analyze Chapter Structure")
        layout.addWidget(analyze_btn)
        
        self.tabs.addTab(tab, "Story Analyzer")

    def clear(self):
        """Clear writer inputs and reset workspace options."""
        self.writer_text.clear()
        self.genre_combo.setCurrentIndex(0)
        self.tone_combo.setCurrentIndex(0)
        if hasattr(self, "analyzer_input"):
            self.analyzer_input.clear()


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        pass

