"""
event_bus.py — Centralized in-memory Pub/Sub event bus for StoryForge.
"""

from typing import Dict, List, Callable, Any
from datetime import datetime

class EventBus:
    """Singleton event bus for synchronous intra-module communication."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._subscribers = {}
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event to all registered subscribers."""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": payload
        }
        
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"[EventBus] Error in subscriber for {event_type}: {e}")

    def clear(self) -> None:
        """Clear all subscribers (mainly for testing)."""
        self._subscribers = {}
