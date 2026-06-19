"""
main_window.py — Top-level application window for StoryForge AI.

Owns the ``StoryManager`` and wires sidebar / editor signals to
manager methods.  Never touches the filesystem directly.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QFileDialog,
)

import uuid
import time
from datetime import datetime

from core.story_manager import StoryManager
from services.memory_extractor import MemoryExtractor
from services.relationship_extractor import RelationshipExtractor
from services.character_profiler import CharacterProfiler
from services.story_analyzer import StoryAnalyzer
from services.consistency_engine import ConsistencyEngine
from services.preference_engine import PreferenceEngine
from services.training_engine import TrainingEngine
from services.context_builder import ContextBuilder
from services.context_ranker import ContextRanker
from services.ai_worker import AIWorker
from services.ai_edit_worker import AIEditWorker
from ui.sidebar import Sidebar
from ui.workspace import Workspace
from utils.constants import APP_NAME


class MainWindow(QMainWindow):
    """
    Application shell: sidebar on the left, editor on the right.

    All filesystem work is delegated to ``StoryManager``.
    """

    def __init__(self) -> None:
        super().__init__()

        # ── Core service (no PySide6 dependency inside) ───────────────
        self._manager = StoryManager()
        self._extractor = MemoryExtractor()
        self._relationship_extractor = RelationshipExtractor()
        self._character_profiler = CharacterProfiler()
        self._story_analyzer = StoryAnalyzer()
        self._consistency_engine = ConsistencyEngine()
        self._preference_engine = PreferenceEngine()
        self._training_engine = TrainingEngine()
        self._context_builder = ContextBuilder()
        self._context_ranker = ContextRanker()
        self._ai_worker = None

        # ── Window setup ──────────────────────────────────────────────
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1000, 650)
        self.resize(1280, 780)

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()

        # Populate sidebar on launch
        self._refresh_sidebar()

    # ══════════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        """Create the splitter layout and status bar."""
        # Sidebar + Workspace split
        self._sidebar = Sidebar()
        self._workspace = Workspace()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._workspace)
        splitter.setStretchFactor(0, 0)   # sidebar: fixed-ish
        splitter.setStretchFactor(1, 1)   # workspace: stretches
        splitter.setSizes([280, 1000])
        splitter.setHandleWidth(1)

        self.setCentralWidget(splitter)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    # ══════════════════════════════════════════════════════════════════
    #  SIGNAL WIRING
    # ══════════════════════════════════════════════════════════════════

    def _connect_signals(self) -> None:
        """Connect sidebar and workspace signals to handler slots."""
        self._sidebar.create_requested.connect(self._on_create)
        self._sidebar.open_requested.connect(self._on_open)
        self._sidebar.delete_requested.connect(self._on_delete)
        self._sidebar.create_universe_requested.connect(self._on_create_universe_requested)
        self._sidebar.import_training_requested.connect(self._on_import_training)
        self._workspace.save_requested.connect(self._on_save)
        self._workspace.chat_message_sent.connect(self._on_chat_send)
        self._workspace.ai_edit_requested.connect(self._on_ai_edit_requested)
        self._workspace.message_action_requested.connect(self._on_message_action_requested)
        self._workspace._memory_view.refresh_requested.connect(self._on_memory_refresh)

    def _setup_shortcuts(self) -> None:
        """Register global keyboard shortcuts."""
        # Ctrl+S  →  save the current story
        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self._on_ctrl_s)

    # ══════════════════════════════════════════════════════════════════
    #  ACTION HANDLERS
    # ══════════════════════════════════════════════════════════════════

    def _on_create(self) -> None:
        """Prompt for title and genre, then create the story on disk."""
        title, ok = QInputDialog.getText(
            self, "Create Story", "Story title:",
        )
        if not ok or not title.strip():
            return

        # Optional genre prompt
        genre, _ = QInputDialog.getText(
            self, "Create Story", "Genre (optional):",
        )

        try:
            story = self._manager.create_story(title, genre.strip())
            self._refresh_sidebar()
            self._show_status(f'Created "{story.title}"')
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Name", str(exc))
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not create story:\n{exc}")

    def _on_open(self, story_id: str) -> None:
        """Load the selected story into the workspace."""
        # Warn if the current story has unsaved changes
        if self._workspace.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Open a different story anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            data = self._manager.load_workspace(story_id)
            self._workspace.load_workspace(data)
            self._show_status(f'Opened "{data.story.title}"')
        except FileNotFoundError:
            QMessageBox.warning(self, "Not Found", "Story could not be found on disk.")
            self._refresh_sidebar()
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not open story:\n{exc}")

    def _on_save(self, story_id: str, content: str) -> None:
        """Persist the editor content to disk."""
        try:
            self._manager.save_story(story_id, content)
            self._on_memory_refresh()
            self._show_status("Story saved ✓")
        except FileNotFoundError:
            QMessageBox.warning(self, "Not Found", "Story could not be found on disk.")
            self._refresh_sidebar()
            self._workspace.clear_workspace()
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not save story:\n{exc}")

    def _on_delete(self, story_id: str) -> None:
        """Confirm, then delete the story from disk."""
        # Find title for the confirmation dialog
        stories = self._manager.list_stories()
        title = next(
            (s.title for s in stories if s.id == story_id),
            "this story",
        )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Delete Story?")
        msg_box.setText(f"Story:\n{title}\n\nThis action cannot be undone.")
        
        btn_delete = msg_box.addButton("Delete", QMessageBox.ButtonRole.AcceptRole)
        btn_cancel = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        if msg_box.clickedButton() != btn_delete:
            return

        try:
            self._manager.delete_story(story_id)
            # If the deleted story was open in the workspace, clear it
            if self._workspace.current_story_id == story_id:
                self._workspace.clear_workspace()
            self._refresh_sidebar()
            self._show_status(f'Deleted "{title}"')
        except FileNotFoundError:
            QMessageBox.warning(self, "Not Found", "Story was already removed.")
            self._refresh_sidebar()
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not delete story:\n{exc}")

    def _on_create_universe_requested(self, story_id: str) -> None:
        """Handle universe creation triggered from a specific story."""
        title, ok = QInputDialog.getText(
            self, "Create Universe", "Universe Name:",
        )
        if not ok or not title.strip():
            return
            
        try:
            uv = self._workspace._universe_view
            u = uv.engine.create_universe(title.strip())
            uv.engine.add_story(u["universe_id"], story_id)
            
            uv._current_universe_id = u["universe_id"]
            uv.refresh_universe_list()
            
            # Switch view to universe if applicable
            if hasattr(self._workspace, "_tabs"):
                self._workspace._tabs.setCurrentWidget(uv)
            
            self._show_status(f'Universe "{title.strip()}" created with story included.')
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not create universe:\n{exc}")

    def _on_ctrl_s(self) -> None:
        """Handle Ctrl+S: trigger save if the workspace has a story loaded."""
        if self._workspace.current_story_id and self._workspace.is_modified:
            self._workspace.trigger_save()

    def _on_chat_send(self, story_id: str, text: str) -> None:
        """Handle sending a message in the chat tab and injecting AI Context."""
        # 1. Save user message
        msg = self._manager.append_chat_message(story_id, "user", text)
        msg_id = msg.get("id")
        self._workspace._chat_view.add_message("user", text, msg["timestamp"], message_id=msg_id)

        # 2. Start generation
        self._start_ai_generation(story_id, text, msg_id)

    def _on_ai_finished(self, story_id: str, diagnostics: dict, parent_id: str, assistant_msg_id: str) -> None:
        self._workspace._chat_view.set_thinking_state(False)
        self._current_bubble.finish_generation()
        
        diag_text = (
            f"Model: {diagnostics['model']}\n"
            f"Prompt Size: {diagnostics['prompt_size']} chars\n"
            f"Context Blocks Used: {diagnostics['context_blocks_used']}\n"
            f"Generation Time: {diagnostics['generation_time_sec']} sec\n"
            f"Response Length: {diagnostics['response_length']} chars\n"
            f"Context Truncated: {diagnostics['context_truncated']}"
        )
        self._current_bubble.set_diagnostics(diag_text)
        
        # Save ONLY the final assistant response to chat history
        self._manager.append_chat_message(
            story_id, "assistant", diagnostics["final_response"],
            message_id=assistant_msg_id, parent_id=parent_id
        )

    def _on_message_action_requested(self, action: str, message_id: str, content: str) -> None:
        story_id = self._workspace.current_story_id
        if not story_id:
            return
            
        if action == "copy":
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(content)
            
        elif action == "add_to_story":
            self._workspace._story_editor.append_text(content)
            self._manager.record_story_insertion(story_id, message_id, content)
            
            # Show badge locally
            for i in range(self._workspace._chat_view._message_layout.count() - 1):
                item = self._workspace._chat_view._message_layout.itemAt(i)
                if item.layout():
                    bubble = item.layout().itemAt(0).widget() or item.layout().itemAt(1).widget()
                    if getattr(bubble, "message_id", None) == message_id:
                        bubble.show_badge()
                        break
                        
        elif action == "locate":
            self._workspace._story_editor.locate_and_highlight(content)
            
        elif action == "variations":
            from services.ai_variation_worker import AIVariationWorker
            
            # Use same ranking logic to fetch context again
            active_universe = None
            if hasattr(self._workspace, "_universe_view"):
                active_universe = self._workspace._universe_view._current_universe_id
            blocks = self._context_builder.build_blocks(content, story_id, active_universe)
            ranked = self._context_ranker.rank_and_filter(content, blocks)
            
            self._var_worker = AIVariationWorker(content, ranked, self)
            self._var_worker.variations_finished.connect(self._on_variations_finished)
            self._var_worker.variations_failed.connect(
                lambda err: QMessageBox.warning(self, "Error", f"Failed to create variations:\n{err}")
            )
            self._var_worker.start()
            self._show_status("Generating variations...")

        elif action == "delete_message":
            history = self._manager.load_chat_history(story_id)
            target_msg = next((m for m in history if m.get("id") == message_id), None)
            
            if target_msg and target_msg.get("story_insertions"):
                self._handle_delete_with_insertions(story_id, message_id, target_msg.get("story_insertions"))
            else:
                reply = QMessageBox.question(
                    self, "Delete Message",
                    "Delete this AI response?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._manager.delete_chat_message_and_children(story_id, message_id)
                    self._workspace._chat_view.load_history(story_id, self._manager.load_chat_history(story_id))
            
        elif action == "delete_conversation":
            history = self._manager.load_chat_history(story_id)
            child_msg = next((m for m in history if m.get("parent_id") == message_id), None)
            
            if child_msg and child_msg.get("story_insertions"):
                self._handle_delete_with_insertions(story_id, message_id, child_msg.get("story_insertions"))
            else:
                reply = QMessageBox.question(
                    self, "Delete Conversation",
                    "Delete this conversation pair?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._manager.delete_chat_message_and_children(story_id, message_id)
                    self._workspace._chat_view.load_history(story_id, self._manager.load_chat_history(story_id))
            
        elif action == "edit_prompt":
            from ui.edit_prompt_dialog import EditPromptDialog
            dialog = EditPromptDialog(content, self)
            dialog.exec()
            if dialog.accepted_action:
                self._manager.update_chat_message(story_id, message_id, dialog.new_text)
                
                # Strip old children
                history = self._manager.load_chat_history(story_id)
                new_history = [m for m in history if m.get("parent_id") != message_id]
                self._manager._write_json(self._manager._find_story_by_id(story_id).chat_history_path, new_history)
                
                # Reload UI
                self._workspace._chat_view.load_history(story_id, new_history)
                
                # Generate new response
                self._start_ai_generation(story_id, dialog.new_text, message_id)

    def _handle_delete_with_insertions(self, story_id: str, message_id: str, insertions: list) -> None:
        if not insertions:
            return
            
        text = insertions[0]
        match = self._workspace._story_editor.find_closest_match(text)
        status = match["status"]
        
        if status == "exact":
            reply = QMessageBox.question(
                self, "Story Overlap",
                "This content exists in your story.\n\nAlso remove it from the story?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                for t in insertions:
                    self._workspace._story_editor.remove_text(t)
                    
        elif status == "slightly_modified":
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Story Overlap")
            msg_box.setText("This content has been modified.")
            
            btn_orig = msg_box.addButton("Delete Original Insertion", QMessageBox.ButtonRole.AcceptRole)
            btn_chat_only = msg_box.addButton("Delete Chat Only", QMessageBox.ButtonRole.RejectRole)
            btn_cancel = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.exec()
            clicked = msg_box.clickedButton()
            if clicked == btn_cancel:
                return
            elif clicked == btn_orig:
                for t in insertions:
                    self._workspace._story_editor.remove_text(t)
                    
        elif status in ["heavily_modified", "missing"]:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Story Overlap")
            msg_box.setText("This content has been significantly modified since insertion.\nAutomatic deletion may remove user-written content.")
            
            btn_chat_only = msg_box.addButton("Delete Chat Only", QMessageBox.ButtonRole.AcceptRole)
            btn_locate = msg_box.addButton("Locate In Story", QMessageBox.ButtonRole.ActionRole)
            btn_cancel = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.exec()
            clicked = msg_box.clickedButton()
            if clicked == btn_cancel:
                return
            elif clicked == btn_locate:
                self._workspace._story_editor.locate_and_highlight(text)
                return # Do not delete chat yet

        # Execute chat deletion
        self._manager.delete_chat_message_and_children(story_id, message_id)
        self._workspace._chat_view.load_history(story_id, self._manager.load_chat_history(story_id))

    def _start_ai_generation(self, story_id: str, text: str, msg_id: str) -> None:
        t_start = time.time()
        active_universe = None
        if hasattr(self._workspace, "_universe_view"):
            active_universe = self._workspace._universe_view._current_universe_id
            
        blocks = self._context_builder.build_blocks(text, story_id, active_universe)
        ranked = self._context_ranker.rank_and_filter(text, blocks)
        
        # Build prompt string explicitly for inspector
        from services.ai_service import AIService
        final_prompt = AIService().build_prompt(text, ranked.get("selected", []))
        
        t_latency = (time.time() - t_start) * 1000
        self._workspace._context_inspector.load_data(ranked, t_latency, final_prompt)
        
        self._workspace._chat_view.set_thinking_state(True)
        timestamp = datetime.now().isoformat()
        assistant_msg_id = str(uuid.uuid4())
        self._current_bubble = self._workspace._chat_view.add_message(
            "assistant", "", timestamp, message_id=assistant_msg_id, parent_id=msg_id
        )
        
        self._ai_worker = AIWorker(text, ranked)
        self._ai_worker.processing_update.connect(self._current_bubble.append_processing)
        self._ai_worker.thinking_chunk.connect(self._current_bubble.append_thinking)
        self._ai_worker.response_chunk.connect(self._current_bubble.append_response)
        self._ai_worker.stats_update.connect(self._current_bubble.update_stats)
        
        self._ai_worker.generation_finished.connect(
            lambda diags: self._on_ai_finished(story_id, diags, msg_id, assistant_msg_id)
        )
        self._ai_worker.start()

    def _on_variations_finished(self, variations: dict) -> None:
        self._show_status("Variations ready.")
        from ui.draft_variations_dialog import DraftVariationsDialog
        dialog = DraftVariationsDialog(variations, self)
        dialog.exec()
        if dialog.action_result == "use":
            self._workspace._story_editor.append_text(dialog.selected_variation_text)

    def _on_ai_edit_requested(self, action: str, selected_text: str, cursor) -> None:
        """Handle AI editing requests from the Story Editor."""
        story_id = self._workspace.current_story_id
        if not story_id:
            return

        try:
            # Rebuild workspace context quickly to rank blocks
            active_universe = None
            if hasattr(self._workspace, "_universe_view"):
                active_universe = self._workspace._universe_view._current_universe_id
                
            blocks = self._context_builder.build_blocks(selected_text, story_id, active_universe)
            ranked = self._context_ranker.rank(selected_text, blocks, max_tokens=1500)
            
            # Start background worker
            t_start = time.time()
            self._edit_worker = AIEditWorker(action, selected_text, ranked, self)
            
            is_append = (action == "continue_writing")
            
            # We capture the cursor in a lambda so apply_ai_edit can use it
            self._edit_worker.edit_finished.connect(
                lambda orig, new_t: self._workspace._story_editor.apply_ai_edit(cursor, orig, new_t, is_append)
            )
            
            t_latency = (time.time() - t_start) * 1000
            from services.ai_service import AIService
            ai_svc = AIService()
            sys_prompt = ai_svc.get_edit_system_prompt(action)
            usr_prompt = ai_svc.build_edit_prompt_content(selected_text, ranked.get("selected", []))
            final_prompt = f"=== SYSTEM ===\n{sys_prompt}\n\n=== USER ===\n{usr_prompt}"
            self._workspace._context_inspector.load_data(ranked, t_latency, final_prompt)
            
            self._edit_worker.edit_failed.connect(
                lambda err: self._workspace._story_editor.set_ai_status(f"⚠️ {err}")
            )
            
            self._edit_worker.start()
        except Exception as e:
            self._workspace._story_editor.set_ai_status(f"⚠️ Failed to start: {str(e)}")

    def _on_memory_refresh(self) -> None:
        """Manually trigger memory extraction and refresh the view."""
        story_id = self._workspace.current_story_id
        if not story_id:
            return
            
        content = self._workspace._story_editor._text_edit.toPlainText()
        memory_dict = self._extractor.extract(content)
        
        # Day 6: Relationship Extraction
        relationships = self._relationship_extractor.extract_relationships(content, memory_dict)
        memory_dict["relationships"] = relationships
        
        # Day 7: Character Profiling
        self._character_profiler.profile_all_characters(content, memory_dict)
        
        # Day 8: Story Analysis
        analysis_dict = self._story_analyzer.analyze_story(memory_dict)
        
        # Day 9: Consistency Engine
        consistency_dict = self._consistency_engine.check_consistency(memory_dict, analysis_dict)
        
        # Day 10: Preference Learning Engine
        user_profile = self._manager.load_user_profile()
        story_metadata = {
            "id": self._manager._find_story_by_id(story_id).id,
            "genre": self._manager._find_story_by_id(story_id).genre
        }
        updated_profile = self._preference_engine.learn_from_story(
            user_profile, story_metadata, memory_dict, analysis_dict, consistency_dict
        )
        
        self._manager.update_memory(story_id, memory_dict)
        self._manager.update_analysis(story_id, analysis_dict)
        self._manager.update_consistency(story_id, consistency_dict)
        self._manager.update_user_profile(updated_profile)
        
        self._workspace._memory_view.load_data(memory_dict)
        self._workspace._analysis_view.load_data(analysis_dict, consistency_dict)
        self._workspace._preferences_view.load_data(updated_profile)
        self._show_status("Extraction, Analysis, Consistency, and Learning complete.")

    def _on_import_training(self) -> None:
        """Handle training document import."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Training Document",
            "",
            "Documents (*.txt *.md *.docx *.pdf)"
        )
        if not files:
            return
            
        import time
        start = time.time()
        
        training_profile = self._manager.load_training_profile()
        from pathlib import Path
        for file in files:
            path = Path(file)
            training_profile = self._training_engine.process_document(path, training_profile)
            
        self._manager.update_training_profile(training_profile)
        
        # If workspace is open, update training view
        if self._workspace.current_story_id:
            self._workspace._training_view.load_data(training_profile)
            
        dur = time.time() - start
        self._show_status(f"Processed {len(files)} document(s) in {dur:.2f}s")

    # ══════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════

    def _refresh_sidebar(self) -> None:
        """Reload the story list from disk and repopulate the sidebar."""
        stories = self._manager.list_stories()
        self._sidebar.refresh(stories)

    def _show_status(self, message: str, timeout_ms: int = 4000) -> None:
        """Display a transient message in the status bar."""
        self._status_bar.showMessage(message, timeout_ms)

    def closeEvent(self, event) -> None:
        """Handle application close event by cleanly terminating background threads."""
        # 1. Stop the training queue manager thread (which is inside Workspace)
        if hasattr(self, "_workspace") and self._workspace:
            # Tell queue manager to stop and wait
            if hasattr(self._workspace, "_training_view") and self._workspace._training_view:
                training_view = self._workspace._training_view
                if hasattr(training_view, "queue_manager") and training_view.queue_manager:
                    training_view.queue_manager.stop_manager()
                    training_view.queue_manager.quit()
                    training_view.queue_manager.wait()
            
            # Stop any dataset lab workers
            if hasattr(self._workspace, "_dataset_lab_view") and self._workspace._dataset_lab_view:
                lab_view = self._workspace._dataset_lab_view
                # Primary import/extract worker
                if hasattr(lab_view, "worker") and lab_view.worker:
                    if lab_view.worker.isRunning():
                        lab_view.worker.cancel()
                        lab_view.worker.quit()
                        lab_view.worker.wait()
                # Pattern extraction worker
                if hasattr(lab_view, "pattern_view") and lab_view.pattern_view:
                    pat_view = lab_view.pattern_view
                    if hasattr(pat_view, "worker") and pat_view.worker:
                        if pat_view.worker.isRunning():
                            pat_view.worker.cancel()
                            pat_view.worker.quit()
                            pat_view.worker.wait()
                # Pilot worker
                if hasattr(lab_view, "pilot_view") and lab_view.pilot_view:
                    pil_view = lab_view.pilot_view
                    if hasattr(pil_view, "worker") and pil_view.worker:
                        if pil_view.worker.isRunning():
                            pil_view.worker.cancel()
                            pil_view.worker.quit()
                            pil_view.worker.wait()
                            
            # Stop evaluation worker
            if hasattr(self._workspace, "_evaluation_view") and self._workspace._evaluation_view:
                eval_view = self._workspace._evaluation_view
                if hasattr(eval_view, "worker") and eval_view.worker:
                    if eval_view.worker.isRunning():
                        eval_view.worker.terminate()
                        eval_view.worker.wait()
        
        # 2. Stop any active AI generation/edit workers in MainWindow
        if hasattr(self, "_ai_worker") and self._ai_worker and self._ai_worker.isRunning():
            self._ai_worker.disconnect()
            self._ai_worker.terminate()
            self._ai_worker.wait()
            
        if hasattr(self, "_edit_worker") and self._edit_worker and self._edit_worker.isRunning():
            self._edit_worker.disconnect()
            self._edit_worker.terminate()
            self._edit_worker.wait()
            
        if hasattr(self, "_var_worker") and self._var_worker and self._var_worker.isRunning():
            self._var_worker.disconnect()
            self._var_worker.terminate()
            self._var_worker.wait()
            
        event.accept()
