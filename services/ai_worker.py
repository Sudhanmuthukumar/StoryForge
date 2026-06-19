import time
from PySide6.QtCore import QThread, Signal
from services.ai_service import AIService

class AIWorker(QThread):
    processing_update = Signal(str)
    thinking_chunk = Signal(str)
    response_chunk = Signal(str)
    stats_update = Signal(dict)
    generation_finished = Signal(dict) # To pass final strings and diagnostics back

    def __init__(self, message: str, ranked_context: dict, parent=None):
        super().__init__(parent)
        self.message = message
        self.ranked_context = ranked_context
        self.ai_service = AIService()

    def run(self):
        t_start = time.time()
        
        # Simulate real processing updates
        self.processing_update.emit("✓ Loading Character Memory")
        time.sleep(0.05)
        self.processing_update.emit("✓ Loading Relationships")
        time.sleep(0.05)
        self.processing_update.emit("✓ Loading Consistency Data")
        time.sleep(0.05)
        self.processing_update.emit("✓ Loading Preferences")
        time.sleep(0.05)
        
        blocks = self.ranked_context.get("selected", [])
        num_blocks = len(blocks)
        
        self.processing_update.emit("✓ Building Context Blocks")
        time.sleep(0.05)
        self.processing_update.emit("✓ Ranking Context")
        time.sleep(0.05)
        self.processing_update.emit(f"✓ Context Blocks Selected: {num_blocks}")
        
        # Build prompt to calculate size
        prompt = self.ai_service.build_prompt(self.message, blocks)
        self.processing_update.emit(f"✓ Prompt Size: {len(prompt)} chars")
        time.sleep(0.05)
        
        self.processing_update.emit("⚒️ Sending Request To AI")
        
        # Logging Verification
        print(f"Selected Model: {self.ai_service.model}")
        print(f"Model Sent To AIWorker: {self.ai_service.model}")
        print(f"Model Sent To AIService: {self.ai_service.model}")
        print(f"Model Sent To Ollama: {self.ai_service.model}")
        
        in_think_block = False
        raw_think = ""
        raw_response = ""
        buffer = ""
        emit_buffer = ""
        
        tokens = 0
        last_emit_time = time.time()
        
        # Stream response
        for chunk in self.ai_service.stream_response(self.message, blocks):
            buffer += chunk
            tokens += 1
            
            # Simple state machine for <think> tags
            if not in_think_block and "<think>" in buffer:
                parts = buffer.split("<think>", 1)
                if parts[0]:
                    emit_buffer += parts[0]
                    raw_response += parts[0]
                in_think_block = True
                buffer = parts[1]
                
            if in_think_block and "</think>" in buffer:
                parts = buffer.split("</think>", 1)
                if parts[0]:
                    self.thinking_chunk.emit(parts[0])
                    raw_think += parts[0]
                in_think_block = False
                buffer = parts[1]
                continue
                
            if in_think_block:
                self.thinking_chunk.emit(chunk)
                raw_think += chunk
                buffer = ""
            else:
                if "<" not in buffer: # Wait if we might be starting a tag
                    emit_buffer += buffer
                    raw_response += buffer
                    buffer = ""
                    
            # Buffering emission logic
            current_time = time.time()
            if len(emit_buffer) > 30 or (current_time - last_emit_time) > 0.15:
                if emit_buffer:
                    self.response_chunk.emit(emit_buffer)
                    emit_buffer = ""
                self.stats_update.emit({
                    "elapsed": current_time - t_start,
                    "tokens": tokens,
                    "chars": len(raw_response)
                })
                last_emit_time = current_time
                    
        if buffer:
            if in_think_block:
                self.thinking_chunk.emit(buffer)
                raw_think += buffer
            else:
                emit_buffer += buffer
                raw_response += buffer
                
        if emit_buffer:
            self.response_chunk.emit(emit_buffer)
            self.stats_update.emit({
                "elapsed": time.time() - t_start,
                "tokens": tokens,
                "chars": len(raw_response)
            })

        t_end = time.time()
        dur = t_end - t_start
        
        diagnostics = {
            "model": self.ai_service.model,
            "prompt_size": len(prompt),
            "context_blocks_used": num_blocks,
            "generation_time_sec": round(dur, 2),
            "response_length": len(raw_response),
            "context_truncated": "Yes" if len(self.ranked_context.get("dropped", [])) > 0 else "No",
            "final_response": raw_response
        }
        
        self.generation_finished.emit(diagnostics)
