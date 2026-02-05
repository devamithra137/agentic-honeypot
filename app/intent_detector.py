"""
Scam Intent Detection Module
Combines keyword-based heuristics with optional LLM reasoning
"""

import os
import logging
from typing import Dict, List
import re

logger = logging.getLogger(__name__)

class IntentDetector:
    """
    Detects scam intent using multiple strategies:
    1. Keyword-based heuristics (primary, fast, reliable)
    2. LLM-based reasoning (secondary, fallback to rules if unavailable)
    """
    
    # Comprehensive scam keyword patterns
    SCAM_KEYWORDS = [
        # Account/Security threats
        r'\b(account|profile)\s+(blocked|suspended|locked|frozen|deactivated|compromised)\b',
        r'\bsuspicious\s+activity\b',
        r'\bunauthorized\s+(access|transaction|login)\b',
        r'\bverify\s+(your|account|identity|details)\b',
        r'\bsecurity\s+(alert|warning|breach)\b',
        
        # Urgency/Pressure
        r'\b(urgent|immediate|immediately|within\s+\d+\s+hours?|act\s+now)\b',
        r'\b(last\s+chance|final\s+(warning|notice)|expire[sd]?)\b',
        r'\blimited\s+time\b',
        
        # Financial demands
        r'\b(pay|payment|transfer|send)\s+(now|immediately|urgently)\b',
        r'\bbank\s+(account|details|information)\b',
        r'\b(credit|debit)\s+card\s+(number|details|info)\b',
        r'\bOTP\b',
        r'\bone\s+time\s+password\b',
        r'\bCVV\b',
        r'\bPIN\b',
        
        # Prizes/Offers (too good to be true)
        r'\b(won|winner|congratulations).*(prize|lottery|reward)\b',
        r'\bfree\s+(money|gift|iPhone|laptop)\b',
        r'\bclaim\s+(your|prize|reward)\b',
        
        # KYC/Verification scams
        r'\bKYC\s+(update|verification|required|pending|incomplete)\b',
        r'\bupdate\s+(your|account|banking)\s+(details|information)\b',
        r'\bconfirm\s+(your|identity|details)\b',
        
        # Phishing indicators
        r'\bclick\s+(here|link|below)\b',
        r'\bdownload\s+(app|application|certificate)\b',
        r'\binstall\s+(app|application|software)\b',
        
        # Payment methods
        r'\bUPI\s+ID\b',
        r'\bGoogle\s+Pay\b',
        r'\bPhonePe\b',
        r'\bPaytm\b',
        r'\bcrypto\s*currency\b',
        r'\bbitcoin\b',
        
        # Impersonation
        r'\b(bank|government|tax|police|court)\s+(official|representative|officer)\b',
        r'\bcustomer\s+(support|service|care)\b',
        r'\btechnical\s+support\b',
    ]
    
    def __init__(self):
        """Initialize the intent detector"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SCAM_KEYWORDS]
        
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set. Using keyword-based detection only.")
    
    def detect_scam(self, context: Dict) -> bool:
        """
        Main detection method.
        
        Args:
            context: Dictionary with 'message' and 'history'
        
        Returns:
            bool: True if scam detected, False otherwise
        """
        try:
            message = context.get("message", "")
            history = context.get("history", [])
            
            # Strategy 1: Keyword-based detection (primary)
            keyword_result = self._keyword_detection(message, history)
            
            if keyword_result:
                logger.info("Scam detected via keyword matching")
                return True
            
            # Strategy 2: LLM-based detection (if available)
            if self.openai_api_key:
                try:
                    llm_result = self._llm_detection(message, history)
                    if llm_result:
                        logger.info("Scam detected via LLM analysis")
                        return True
                except Exception as e:
                    logger.warning(f"LLM detection failed: {e}. Falling back to keyword result.")
            
            # Default: not a scam
            return False
            
        except Exception as e:
            logger.error(f"Error in scam detection: {e}")
            # Fail safe: return False to avoid false positives
            return False
    
    def _keyword_detection(self, message: str, history: List) -> bool:
        """
        Keyword-based heuristic detection.
        Checks current message and recent history for scam patterns.
        """
        # Check current message
        for pattern in self.compiled_patterns:
            if pattern.search(message):
                return True
        
        # Check recent history (last 3 messages) for context
        recent_messages = history[-3:] if len(history) > 3 else history
        for msg in recent_messages:
            content = msg.get("content", "") if isinstance(msg, dict) else ""
            for pattern in self.compiled_patterns:
                if pattern.search(content):
                    return True
        
        return False
    
    def _llm_detection(self, message: str, history: List) -> bool:
        """
        LLM-based detection using OpenAI API.
        Fallback: returns False on any error.
        """
        try:
            import openai
            
            # Prepare context
            history_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in (history[-5:] if len(history) > 5 else history)
            ])
            
            prompt = f"""You are a scam detection system. Analyze if the following message is a scam attempt.

Conversation history:
{history_text}

Current message: {message}

Is this a scam attempt? Respond with only 'YES' or 'NO'."""

            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a scam detection expert. Respond only with YES or NO."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip().upper()
            return "YES" in result
            
        except ImportError:
            logger.warning("OpenAI library not installed")
            return False
        except Exception as e:
            logger.warning(f"LLM detection error: {e}")
            return False
