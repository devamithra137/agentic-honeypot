"""
Agentic Honey-Pot – AI Scam Engagement System
Main FastAPI Application Entry Point
"""


from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

API_KEY = os.getenv("API_KEY")



from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.models import HoneypotRequest, HoneypotResponse
from app.intent_detector import IntentDetector
from app.agent import ScamEngagementAgent
from app.intelligence_extractor import IntelligenceExtractor
from app.conversation_manager import ConversationManager
from app.response_builder import ResponseBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state (in-memory)
conversation_manager = None
intent_detector = None
agent = None
intelligence_extractor = None
response_builder = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup"""
    global conversation_manager, intent_detector, agent, intelligence_extractor, response_builder
    
    logger.info("Initializing Agentic Honey-Pot system...")
    
    # Initialize all components
    conversation_manager = ConversationManager()
    intent_detector = IntentDetector()
    agent = ScamEngagementAgent()
    intelligence_extractor = IntelligenceExtractor()
    response_builder = ResponseBuilder()
    
    logger.info("System initialization complete")
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Agentic Honey-Pot system...")

# Create FastAPI app
app = FastAPI(
    title="Agentic Honey-Pot API",
    description="AI Scam Engagement System",
    version="1.0.0",
    lifespan=lifespan
)

# Security
security = HTTPBearer()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    logger.warning("API_KEY environment variable not set! Authentication will fail.")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify Bearer token against API_KEY environment variable"""
    if not API_KEY:
        logger.error("API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )
    
    if credentials.credentials != API_KEY:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agentic-honeypot"}

@app.post("/api/agentic-honeypot", response_model=HoneypotResponse)
async def agentic_honeypot(
    request: HoneypotRequest,
    authenticated: bool = Depends(verify_api_key)
) -> JSONResponse:
    """
    Main endpoint for the Agentic Honey-Pot system.
    
    This endpoint:
    1. Detects scam intent in incoming messages
    2. Activates an AI agent if scam is detected
    3. Maintains multi-turn conversations
    4. Extracts actionable intelligence
    5. Returns structured JSON response
    
    NEVER crashes - always returns valid JSON even on errors.
    """
    
    try:
        logger.info(f"Processing request for conversation: {request.conversation_id}")
        
        # Step 1: Get or create conversation state
        conversation_state = conversation_manager.get_or_create(request.conversation_id)
        
        # Step 2: Detect scam intent
        # Combine current message with history for better context
        full_context = {
            "message": request.message,
            "history": request.history or []
        }
        
        scam_detected = intent_detector.detect_scam(full_context)
        logger.info(f"Scam detection result: {scam_detected}")
        
        # Step 3: Update conversation state
        conversation_state["scam_detected"] = conversation_state.get("scam_detected", False) or scam_detected
        conversation_state["turn_count"] = conversation_state.get("turn_count", 0) + 1
        
        # Step 4: Determine if agent should be activated
        agent_activated = conversation_state["scam_detected"]
        
        # Step 5: Generate agent reply
        agent_reply = ""
        if agent_activated:
            agent_reply = agent.generate_response(
                message=request.message,
                history=request.history or [],
                conversation_state=conversation_state
            )
        else:
            # Not a scam, provide neutral response
            agent_reply = agent.generate_neutral_response(request.message)
        
        # Step 6: Extract intelligence from the message
        extracted_intelligence = intelligence_extractor.extract(request.message)
        
        # Step 7: Calculate engagement metrics
        engagement_metrics = conversation_manager.get_metrics(request.conversation_id)
        
        # Step 8: Build the response using ResponseBuilder (single source of truth)
        response = response_builder.build_success_response(
            scam_detected=conversation_state["scam_detected"],
            agent_activated=agent_activated,
            agent_reply=agent_reply,
            engagement_metrics=engagement_metrics,
            extracted_intelligence=extracted_intelligence
        )
        
        logger.info(f"Successfully processed request for conversation: {request.conversation_id}")
        
        return JSONResponse(content=response, status_code=200)
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 401)
        raise
        
    except Exception as e:
        # Catch ANY unexpected error and return safe fallback
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        # Use ResponseBuilder for consistent error responses
        error_response = response_builder.build_error_response(
            error_message=str(e),
            conversation_id=request.conversation_id
        )
        
        return JSONResponse(content=error_response, status_code=200)

# Global exception handler as final safety net
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler - ensures NOTHING crashes the API.
    Returns a safe, valid JSON response for any unhandled exception.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    safe_response = {
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
    
    return JSONResponse(content=safe_response, status_code=200)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
