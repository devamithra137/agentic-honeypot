"""
Conversation Manager
Maintains in-memory conversation state and tracks metrics
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages conversation state in memory.
    
    Tracks:
    - Conversation metadata
    - Turn count
    - Start time for duration calculation
    - Scam detection status
    """
    
    def __init__(self):
        """Initialize conversation storage"""
        self.conversations: Dict[str, Dict] = {}
    
    def get_or_create(self, conversation_id: str) -> Dict:
        """
        Get existing conversation state or create new one.
        
        Args:
            conversation_id: Unique conversation identifier
        
        Returns:
            Dict: Conversation state
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "conversation_id": conversation_id,
                "start_time": datetime.now(),
                "turn_count": 0,
                "scam_detected": False,
                "agent_activated": False,
                "last_updated": datetime.now()
            }
            logger.info(f"Created new conversation: {conversation_id}")
        else:
            # Update last_updated timestamp
            self.conversations[conversation_id]["last_updated"] = datetime.now()
        
        return self.conversations[conversation_id]
    
    def update(self, conversation_id: str, updates: Dict) -> None:
        """
        Update conversation state.
        
        Args:
            conversation_id: Conversation to update
            updates: Dictionary of fields to update
        """
        if conversation_id in self.conversations:
            self.conversations[conversation_id].update(updates)
            self.conversations[conversation_id]["last_updated"] = datetime.now()
    
    def get_metrics(self, conversation_id: str) -> Dict:
        """
        Calculate engagement metrics for a conversation.
        
        Args:
            conversation_id: Conversation identifier
        
        Returns:
            Dict with turn_count and engagement_duration
        """
        if conversation_id not in self.conversations:
            return {
                "turn_count": 1,
                "engagement_duration": "0s"
            }
        
        conv = self.conversations[conversation_id]
        
        # Calculate duration
        start_time = conv.get("start_time", datetime.now())
        duration_seconds = (datetime.now() - start_time).total_seconds()
        
        # Format duration
        duration_str = self._format_duration(duration_seconds)
        
        return {
            "turn_count": conv.get("turn_count", 1),
            "engagement_duration": duration_str
        }
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format.
        
        Examples:
        - 45 seconds -> "45s"
        - 90 seconds -> "1m 30s"
        - 3600 seconds -> "1h"
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds}s"
            return f"{minutes}m"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            if remaining_minutes > 0:
                return f"{hours}h {remaining_minutes}m"
            return f"{hours}h"
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """
        Clean up old conversations to prevent memory bloat.
        Called periodically or on demand.
        
        Args:
            max_age_hours: Maximum age of conversations to keep
        """
        now = datetime.now()
        to_remove = []
        
        for conv_id, conv_data in self.conversations.items():
            last_updated = conv_data.get("last_updated", now)
            age_hours = (now - last_updated).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            del self.conversations[conv_id]
            logger.info(f"Cleaned up old conversation: {conv_id}")
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old conversations")
