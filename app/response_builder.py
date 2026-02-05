"""
Response Builder
Single source of truth for API response structure.
Ensures STRICT compliance with response schema.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class ResponseBuilder:
    """
    Builds standardized responses for the API.
    
    CRITICAL: This is the ONLY place where response structure is defined.
    ALL responses must go through this builder to ensure consistency.
    """
    
    def build_success_response(
        self,
        scam_detected: bool,
        agent_activated: bool,
        agent_reply: str,
        engagement_metrics: Dict,
        extracted_intelligence: Dict
    ) -> Dict:
        """
        Build a successful response.
        
        Args:
            scam_detected: Whether scam was detected
            agent_activated: Whether agent is engaged
            agent_reply: Agent's response message
            engagement_metrics: Dict with turn_count and engagement_duration
            extracted_intelligence: Dict with bank_accounts, upi_ids, phishing_urls
        
        Returns:
            Dict: Properly formatted response
        """
        # Ensure extracted_intelligence has all required keys with empty lists if missing
        intelligence = {
            "bank_accounts": extracted_intelligence.get("bank_accounts", []),
            "upi_ids": extracted_intelligence.get("upi_ids", []),
            "phishing_urls": extracted_intelligence.get("phishing_urls", [])
        }
        
        # Ensure all arrays are lists, not None
        for key in intelligence:
            if intelligence[key] is None:
                intelligence[key] = []
        
        # Ensure engagement_metrics has required fields
        metrics = {
            "turn_count": engagement_metrics.get("turn_count", 1),
            "engagement_duration": engagement_metrics.get("engagement_duration", "0s")
        }
        
        response = {
            "scam_detected": bool(scam_detected),
            "agent_activated": bool(agent_activated),
            "agent_reply": str(agent_reply),
            "engagement_metrics": metrics,
            "extracted_intelligence": intelligence,
            "status": "success"
        }
        
        # Validate response structure before returning
        self._validate_response(response)
        
        return response
    
    def build_error_response(
        self,
        error_message: str = "An error occurred",
        conversation_id: str = None
    ) -> Dict:
        """
        Build an error response that still complies with schema.
        
        IMPORTANT: Even errors must return valid response structure.
        
        Args:
            error_message: Error description (for logging, not exposed)
            conversation_id: Optional conversation ID for context
        
        Returns:
            Dict: Safe error response
        """
        logger.error(f"Error response for conversation {conversation_id}: {error_message}")
        
        # Safe fallback response that never reveals system errors
        response = {
            "scam_detected": False,
            "agent_activated": False,
            "agent_reply": "I'm sorry, I didn't quite understand that. Could you please rephrase?",
            "engagement_metrics": {
                "turn_count": 1,
                "engagement_duration": "0s"
            },
            "extracted_intelligence": {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_urls": []
            },
            "status": "error"
        }
        
        # Validate response structure
        self._validate_response(response)
        
        return response
    
    def _validate_response(self, response: Dict) -> None:
        """
        Validate response structure matches schema.
        Raises ValueError if invalid.
        
        This is a safety check to catch any builder bugs.
        """
        required_keys = {
            "scam_detected": bool,
            "agent_activated": bool,
            "agent_reply": str,
            "engagement_metrics": dict,
            "extracted_intelligence": dict,
            "status": str
        }
        
        # Check all required keys exist
        for key, expected_type in required_keys.items():
            if key not in response:
                raise ValueError(f"Missing required key: {key}")
            
            if not isinstance(response[key], expected_type):
                raise ValueError(f"Invalid type for {key}: expected {expected_type}, got {type(response[key])}")
        
        # Validate engagement_metrics structure
        metrics = response["engagement_metrics"]
        if "turn_count" not in metrics or "engagement_duration" not in metrics:
            raise ValueError("Invalid engagement_metrics structure")
        
        if not isinstance(metrics["turn_count"], int):
            raise ValueError("turn_count must be int")
        
        if not isinstance(metrics["engagement_duration"], str):
            raise ValueError("engagement_duration must be str")
        
        # Validate extracted_intelligence structure
        intelligence = response["extracted_intelligence"]
        required_intel_keys = ["bank_accounts", "upi_ids", "phishing_urls"]
        
        for key in required_intel_keys:
            if key not in intelligence:
                raise ValueError(f"Missing intelligence key: {key}")
            
            if not isinstance(intelligence[key], list):
                raise ValueError(f"{key} must be a list, got {type(intelligence[key])}")
        
        # Validate status value
        if response["status"] not in ["success", "error"]:
            raise ValueError(f"Invalid status value: {response['status']}")
        
        logger.debug("Response validation passed")
