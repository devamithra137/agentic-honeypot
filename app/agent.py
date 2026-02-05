"""
Scam Engagement Agent
Maintains believable human persona while engaging scammers
"""

import os
import logging
import random
from typing import List, Dict

logger = logging.getLogger(__name__)

class ScamEngagementAgent:
    """
    Autonomous AI agent that engages with scammers.
    
    Strategy:
    1. Maintain believable human persona (confused, concerned, cooperative)
    2. Ask clarifying questions to waste scammer's time
    3. Strategically request payment/verification details
    4. Never reveal detection
    5. Keep scammer engaged for intelligence extraction
    """
    
    # Persona templates for believable responses
    CONCERNED_RESPONSES = [
        "Oh no! This is really concerning. What exactly do I need to do?",
        "I'm worried about my account. Can you help me understand what happened?",
        "This is very worrying. How do I fix this issue?",
        "I don't want to lose access to my account. What should I do next?",
        "That sounds serious! What steps do I need to take?",
    ]
    
    CONFUSED_RESPONSES = [
        "I'm not sure I understand. Can you explain this again?",
        "Wait, I'm a bit confused. What exactly is the problem?",
        "Sorry, I'm not very tech-savvy. Can you walk me through this slowly?",
        "I'm not sure what you mean. Could you provide more details?",
        "This is confusing to me. What do you need from me exactly?",
    ]
    
    COOPERATIVE_RESPONSES = [
        "Okay, I'm ready to help. What information do you need?",
        "I want to resolve this. What details do you require?",
        "I'm willing to cooperate. What should I send you?",
        "Let me help fix this. What do you need from me?",
        "I'll do whatever is needed. What are the next steps?",
    ]
    
    VERIFICATION_QUESTIONS = [
        "Before I proceed, can you confirm which bank this is regarding?",
        "Just to verify, what is the exact account number you're referring to?",
        "For security, where should I send the payment to?",
        "What is the official payment method I should use?",
        "Can you provide the UPI ID or account details where I should transfer?",
        "What is the exact amount I need to pay to resolve this?",
        "Is there a reference number or transaction ID for this?",
    ]
    
    DELAY_TACTICS = [
        "I need to check my bank app first. Can you give me a minute?",
        "Let me find my card details. Hold on a moment.",
        "I'm at work right now. Can I call you back in an hour?",
        "My phone battery is low. Can we continue this later?",
        "I need to consult with my family first. Is that okay?",
    ]
    
    def __init__(self):
        """Initialize the engagement agent"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            logger.info("OPENAI_API_KEY not set. Using template-based responses only.")
    
    def generate_response(self, message: str, history: List, conversation_state: Dict) -> str:
        """
        Generate agent response based on conversation state.
        
        Strategy:
        - Early turns: Express concern, ask questions
        - Mid turns: Show confusion, request clarification
        - Later turns: Become more cooperative, request payment details
        
        Args:
            message: Current scammer message
            history: Conversation history
            conversation_state: Current state of conversation
        
        Returns:
            str: Agent's response
        """
        try:
            turn_count = conversation_state.get("turn_count", 1)
            
            # Try LLM-based response first if available
            if self.openai_api_key:
                try:
                    llm_response = self._llm_generate_response(message, history, turn_count)
                    if llm_response:
                        return llm_response
                except Exception as e:
                    logger.warning(f"LLM response generation failed: {e}. Using template.")
            
            # Fallback to template-based response
            return self._template_based_response(message, turn_count)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I see. Can you tell me more about this?"
    
    def _template_based_response(self, message: str, turn_count: int) -> str:
        """
        Generate response using templates based on conversation stage.
        RELIABLE fallback that never fails.
        """
        # Stage 1: Early engagement (turns 1-2) - Show concern
        if turn_count <= 2:
            return random.choice(self.CONCERNED_RESPONSES)
        
        # Stage 2: Mid engagement (turns 3-4) - Show confusion, ask questions
        elif turn_count <= 4:
            if random.random() < 0.6:
                return random.choice(self.CONFUSED_RESPONSES)
            else:
                return random.choice(self.VERIFICATION_QUESTIONS)
        
        # Stage 3: Later engagement (turns 5-6) - Become cooperative
        elif turn_count <= 6:
            if random.random() < 0.7:
                return random.choice(self.COOPERATIVE_RESPONSES)
            else:
                return random.choice(self.VERIFICATION_QUESTIONS)
        
        # Stage 4: Extended engagement (turns 7+) - Mix of cooperation and delays
        else:
            responses = (
                self.COOPERATIVE_RESPONSES + 
                self.VERIFICATION_QUESTIONS + 
                self.DELAY_TACTICS
            )
            return random.choice(responses)
    
    def _llm_generate_response(self, message: str, history: List, turn_count: int) -> str:
        """
        Generate contextual response using LLM.
        Returns None on failure to trigger fallback.
        """
        try:
            import openai
            
            # Build conversation context
            history_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in (history[-5:] if len(history) > 5 else history)
            ])
            
            # System prompt defines agent behavior
            system_prompt = """You are playing the role of a potential scam victim in a honeypot system. Your goal is to keep the scammer engaged while appearing like a real, concerned person.

Rules:
1. Act confused, concerned, or cooperative depending on the situation
2. Ask clarifying questions about payment methods, account details, or verification steps
3. Never reveal you know it's a scam
4. Sound like a real person (use natural language, show emotion)
5. Try to get the scammer to reveal payment details (bank accounts, UPI IDs, phone numbers)
6. Keep responses short (1-2 sentences)
7. Show appropriate concern and urgency

Respond naturally as a potential victim would."""

            user_prompt = f"""Conversation history:
{history_text}

Scammer's message: {message}

Turn count: {turn_count}

Generate a natural response that keeps the scammer engaged. If it's early in the conversation, show concern. If it's later, ask for specific payment or verification details."""

            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=100,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except ImportError:
            logger.warning("OpenAI library not installed")
            return None
        except Exception as e:
            logger.warning(f"LLM response generation error: {e}")
            return None
    
    def generate_neutral_response(self, message: str) -> str:
        """
        Generate neutral response when scam is NOT detected.
        Polite but non-committal.
        """
        neutral_responses = [
            "I see. Is there anything specific you need help with?",
            "Thanks for reaching out. What can I help you with?",
            "I understand. Could you provide more details?",
            "Okay. What would you like to discuss?",
            "I'm here to help. What do you need?",
        ]
        return random.choice(neutral_responses)
