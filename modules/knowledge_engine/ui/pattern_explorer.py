import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QComboBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel)
from PyQt6.QtCore import Qt
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine

class PatternExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StoryForge Pattern Explorer")
        self.setGeometry(100, 100, 900, 600)
        self.ke = KnowledgeEngine()
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top Controls
        controls_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search patterns...")
        self.search_input.textChanged.connect(self.filter_data)
        controls_layout.addWidget(self.search_input)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        for p_type in self.ke.PATTERN_TYPES:
            self.category_combo.addItem(p_type)
        self.category_combo.currentTextChanged.connect(self.filter_data)
        controls_layout.addWidget(self.category_combo)
        
        main_layout.addLayout(controls_layout)
        
        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Category", "Content", "Occurrences", "Provenance"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)
        
        # Status
        self.status_label = QLabel("Loading...")
        main_layout.addWidget(self.status_label)
        
    def load_data(self):
        self.all_patterns = []
        for p_type in self.ke.PATTERN_TYPES:
            patterns = self.ke.read_patterns(p_type)
            self.all_patterns.extend(patterns)
        self.filter_data()
        
    def filter_data(self):
        search_text = self.search_input.text().lower()
        selected_category = self.category_combo.currentText()
        
        filtered = []
        for p in self.all_patterns:
            if selected_category != "All Categories" and p.get("pattern_type") != selected_category:
                continue
            if search_text and search_text not in p.get("content", "").lower() and search_text not in p.get("pattern_id", "").lower():
                continue
            filtered.append(p)
            
        self.table.setRowCount(len(filtered))
        for row, p in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(p.get("pattern_id", "")))
            self.table.setItem(row, 1, QTableWidgetItem(p.get("pattern_type", "")))
            self.table.setItem(row, 2, QTableWidgetItem(p.get("content", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(p.get("occurrence_count", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(p.get("provenance", []))))
            
        self.status_label.setText(f"Showing {len(filtered)} patterns")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PatternExplorer()
    window.show()
    # sys.exit(app.exec())  # We comment out the blocking call for testing if needed
