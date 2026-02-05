"""
Pydantic models for request/response validation
Ensures strict type checking and validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: str = Field(..., description="Role: 'scammer' or 'user'")
    content: str = Field(..., description="Message content")

class HoneypotRequest(BaseModel):
    """
    Request schema for /api/agentic-honeypot endpoint
    Validates all incoming requests
    """
    conversation_id: str = Field(..., description="Unique conversation identifier")
    message: str = Field(..., description="Current message from scammer")
    history: Optional[List[ConversationMessage]] = Field(
        default=None,
        description="Conversation history (optional)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "message": "Your account has been blocked. Click here to verify.",
                "history": [
                    {"role": "scammer", "content": "Hello, this is bank support"},
                    {"role": "user", "content": "Hi, what's the issue?"}
                ]
            }
        }

class EngagementMetrics(BaseModel):
    """Engagement metrics for the conversation"""
    turn_count: int = Field(..., description="Number of turns in conversation")
    engagement_duration: str = Field(..., description="Duration of engagement (e.g., '45s', '2m')")

class ExtractedIntelligence(BaseModel):
    """Extracted scam intelligence"""
    bank_accounts: List[str] = Field(default_factory=list, description="Extracted bank account numbers")
    upi_ids: List[str] = Field(default_factory=list, description="Extracted UPI IDs")
    phishing_urls: List[str] = Field(default_factory=list, description="Extracted phishing URLs")

class HoneypotResponse(BaseModel):
    """
    Response schema for /api/agentic-honeypot endpoint
    STRICT SCHEMA - NEVER modify field names or structure
    """
    scam_detected: bool = Field(..., description="Whether scam intent was detected")
    agent_activated: bool = Field(..., description="Whether AI agent is engaged")
    agent_reply: str = Field(..., description="Agent's response message")
    engagement_metrics: EngagementMetrics = Field(..., description="Conversation metrics")
    extracted_intelligence: ExtractedIntelligence = Field(..., description="Extracted scam data")
    status: Literal["success", "error"] = Field(..., description="Request status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scam_detected": True,
                "agent_activated": True,
                "agent_reply": "Oh no! What should I do to unblock my account?",
                "engagement_metrics": {
                    "turn_count": 3,
                    "engagement_duration": "45s"
                },
                "extracted_intelligence": {
                    "bank_accounts": ["1234567890"],
                    "upi_ids": ["scammer@paytm"],
                    "phishing_urls": ["http://fake-bank.com"]
                },
                "status": "success"
            }
        }
