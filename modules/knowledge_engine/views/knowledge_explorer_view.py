from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLineEdit, QPushButton, QLabel, QSplitter)
from PySide6.QtCore import Qt
from modules.knowledge_engine.services.knowledge_database import KnowledgeDatabase

class KnowledgeExplorerView(QWidget):
    def __init__(self):
        super().__init__()
        self.db = KnowledgeDatabase()
        self._init_ui()
        self.load_database("character_patterns.json")

    def _init_ui(self):
        layout = QHBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Sidebar: Database Selector
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Knowledge Databases</b>"))
        
        self.db_list = QListWidget()
        for db_name in self.db.DB_NAMES:
            self.db_list.addItem(db_name)
        self.db_list.setCurrentRow(0)
        self.db_list.itemClicked.connect(self._on_db_selected)
        left_layout.addWidget(self.db_list)
        
        # Right Area: Data Viewer
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Top Bar: Search & Filter
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search patterns, genres, archetypes...")
        self.search_input.textChanged.connect(self._on_search)
        top_bar.addWidget(self.search_input)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(lambda: self.load_database(self.current_db))
        top_bar.addWidget(refresh_btn)
        
        right_layout.addLayout(top_bar)
        
        # Main Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Category", "Success Score", "Occurrences", "Source Books", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.table)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 800])
        
        layout.addWidget(splitter)
        
        self.current_db = self.db.DB_NAMES[0]
        
    def _on_db_selected(self, item):
        self.current_db = item.text()
        self.load_database(self.current_db)
        
    def _on_search(self, text):
        if not text:
            self.load_database(self.current_db)
            return
            
        results = self.db.search_patterns(self.current_db, text)
        self._populate_table(results)

    def load_database(self, db_name: str):
        data = self.db.read_db(db_name)
        self._populate_table(data)
        
    def _populate_table(self, data):
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("category", "")))
            score = f"{item.get('success_score', 5.0):.1f}/10"
            self.table.setItem(row, 2, QTableWidgetItem(score))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get("occurrence_count", 0))))
            books = ", ".join(item.get("source_books", []))
            self.table.setItem(row, 4, QTableWidgetItem(books))
            self.table.setItem(row, 5, QTableWidgetItem(item.get("description", "")))

    def clear(self):
        """Clear search input and reset Knowledge Explorer view."""
        self.search_input.clear()
        if hasattr(self, "db_list") and self.db_list.count() > 0:
            self.db_list.setCurrentRow(0)
            self.load_database(self.db.DB_NAMES[0])


    def load_data(self, data=None):
        """Adapter for Workspace interface."""
        pass

