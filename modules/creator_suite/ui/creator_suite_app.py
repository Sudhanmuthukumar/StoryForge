import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTextEdit, QLabel, QTabWidget, QHBoxLayout, QLineEdit)
from modules.knowledge_engine.services.knowledge_engine import KnowledgeEngine
from modules.creator_suite.services.story_architect import StoryArchitect
from modules.creator_suite.services.character_forge import CharacterForge
from modules.creator_suite.services.lore_builder import LoreBuilder
from modules.creator_suite.services.quest_generator import QuestGenerator
from modules.creator_suite.services.narrative_analyzer import NarrativeAnalyzer
from modules.creator_suite.services.npc_forge import NPCForge
from modules.creator_suite.services.faction_builder import FactionBuilder
from modules.creator_suite.services.quest_chain_builder import QuestChainBuilder
from modules.creator_suite.services.campaign_builder import CampaignBuilder
from modules.unreal_export.services.unreal_export_layer import UnrealExportLayer

class CreatorSuiteApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StoryForge Creator Suite")
        self.setGeometry(100, 100, 1000, 700)
        
        self.ke = KnowledgeEngine()
        self.exporter = UnrealExportLayer()
        
        # Story Tools
        self.architect = StoryArchitect(self.ke)
        self.forge = CharacterForge(self.ke)
        self.lore = LoreBuilder(self.ke)
        
        # Game Tools
        self.npc = NPCForge(self.ke)
        self.faction = FactionBuilder(self.ke)
        self.quest_chain = QuestChainBuilder(self.ke)
        self.campaign = CampaignBuilder(self.ke)
        
        # Analysis Tools
        self.analyzer = NarrativeAnalyzer(self.ke)
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Main categories
        self.main_tabs = QTabWidget()
        main_layout.addWidget(self.main_tabs)
        
        # Setup Categories
        self.setup_story_tools()
        self.setup_game_tools()
        self.setup_analysis_tools()
        
    def create_generation_tab(self, name, input_label, generator_func, export_category=None):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel(input_label))
        input_field = QLineEdit()
        input_layout.addWidget(input_field)
        layout.addLayout(input_layout)
        
        btn_layout = QHBoxLayout()
        gen_btn = QPushButton(f"Generate {name}")
        btn_layout.addWidget(gen_btn)
        
        export_btn = None
        if export_category:
            export_btn = QPushButton(f"Export to Unreal ({export_category})")
            export_btn.setEnabled(False)
            btn_layout.addWidget(export_btn)
            
        layout.addLayout(btn_layout)
        
        output_area = QTextEdit()
        output_area.setReadOnly(True)
        layout.addWidget(output_area)
        
        self.current_data = None
        
        def on_generate():
            result = generator_func(input_field.text())
            self.current_data = result
            output_area.setText(json.dumps(result, indent=4))
            if export_btn:
                export_btn.setEnabled(True)
                
        def on_export():
            if self.current_data and export_category:
                filename = input_field.text().replace(" ", "_").lower() or "generated"
                
                # Check if it's the intelligent NPC wrapper
                if isinstance(self.current_data, dict) and "npc" in self.current_data and "npc_memory" in self.current_data:
                    self.exporter.export_assets("npcs", filename, [self.current_data["npc"]])
                    self.exporter.export_assets("npc_memory", f"{filename}_memory", [self.current_data["npc_memory"]])
                    self.exporter.export_assets("npc_relationships", f"{filename}_rels", [self.current_data["npc_relationships"]])
                    self.exporter.export_assets("npc_goals", f"{filename}_goals", [self.current_data["npc_goals"]])
                    self.exporter.export_assets("npc_reactions", f"{filename}_reactions", [self.current_data["npc_reactions"]])
                    output_area.append(f"\n[EXPORT SUCCESS] Exported intelligent NPC components to 5 separate datasets.")
                else:
                    data_list = [self.current_data] if isinstance(self.current_data, dict) else self.current_data
                    self.exporter.export_assets(export_category, filename, data_list)
                    output_area.append(f"\n[EXPORT SUCCESS] Exported to {export_category}")
                
        gen_btn.clicked.connect(on_generate)
        if export_btn:
            export_btn.clicked.connect(on_export)
            
        return tab

    def setup_story_tools(self):
        story_tabs = QTabWidget()
        story_tabs.addTab(self.create_generation_tab("Story Architect", "Prompt:", lambda t: self.architect.generate_outline(t or "A new adventure")), "Architect")
        story_tabs.addTab(self.create_generation_tab("Character Forge", "Archetype:", lambda t: self.forge.generate_character(t or "Hero")), "Character")
        story_tabs.addTab(self.create_generation_tab("Lore Builder", "Topic:", lambda t: self.lore.generate_lore(t or "Lost Kingdom")), "Lore")
        
        self.main_tabs.addTab(story_tabs, "Story Tools")

    def setup_game_tools(self):
        game_tabs = QTabWidget()
        
        game_tabs.addTab(self.create_generation_tab("Intelligent NPC Forge", "Role:", lambda t: self.npc.generate_npc(t or "Merchant", generate_intelligence=True), export_category="npcs"), "NPCs")
        game_tabs.addTab(self.create_generation_tab("Faction Builder", "Archetype:", lambda t: self.faction.generate_faction(t or "Zealots"), export_category="factions"), "Factions")
        game_tabs.addTab(self.create_generation_tab("Quest Chain", "Theme:", lambda t: self.quest_chain.generate_chain(t or "The Awakening"), export_category="quests"), "Quest Chains")
        game_tabs.addTab(self.create_generation_tab("Campaign", "Title:", lambda t: self.campaign.build_campaign(t or "Epic Campaign"), export_category="campaigns"), "Campaign")
        
        self.main_tabs.addTab(game_tabs, "Game Tools")

    def setup_analysis_tools(self):
        analysis_tabs = QTabWidget()
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Paste text to analyze:"))
        text_input = QTextEdit()
        layout.addWidget(text_input)
        
        btn = QPushButton("Analyze Narrative")
        output_area = QTextEdit()
        output_area.setReadOnly(True)
        
        def on_click():
            result = self.analyzer.analyze_text(text_input.toPlainText())
            output_area.setText(json.dumps(result, indent=4))
            
        btn.clicked.connect(on_click)
        layout.addWidget(btn)
        layout.addWidget(output_area)
        
        analysis_tabs.addTab(tab, "Narrative Analyzer")
        self.main_tabs.addTab(analysis_tabs, "Analysis")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CreatorSuiteApp()
    window.show()
