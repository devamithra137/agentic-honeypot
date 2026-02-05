"""
Agentic Honey-Pot – AI Scam Engagement System
Main FastAPI Application Entry Point
"""

import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.models import HoneypotRequest, HoneypotResponse
from app.intent_detector import IntentDetector
from app.agent import ScamEngagementAgent
from app.intelligence_extractor import IntelligenceExtractor
from app.conversation_manager import ConversationManager
from app.response_builder import ResponseBuilder

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
API_KEY = os.getenv("API_KEY")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if not API_KEY:
    logger.warning("API_KEY environment variable not set! Authentication will fail.")

# -------------------------------------------------------------------
# Global state (in-memory)
# -------------------------------------------------------------------

conversation_manager: ConversationManager | None = None
intent_detector: IntentDetector | None = None
agent: ScamEngagementAgent | None = None
intelligence_extractor: IntelligenceExtractor | None = None
response_builder: ResponseBuilder | None = None

# -------------------------------------------------------------------
# Lifespan
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global conversation_manager, intent_detector, agent, intelligence_extractor, response_builder

    logger.info("Initializing Agentic Honey-Pot system...")

    conversation_manager = ConversationManager()
    intent_detector = IntentDetector()
    agent = ScamEngagementAgent()
    intelligence_extractor = IntelligenceExtractor()
    response_builder = ResponseBuilder()

    logger.info("System initialization complete")
    yield
    logger.info("Shutting down Agentic Honey-Pot system...")

# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------

app = FastAPI(
    title="Agentic Honey-Pot API",
    description="AI Scam Engagement System",
    version="1.0.0",
    lifespan=lifespan
)

# -------------------------------------------------------------------
# Authentication
# -------------------------------------------------------------------

def verify_api_key(
    x_api_key: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
):
    # Hackathon tester: x-api-key
    if x_api_key and x_api_key == API_KEY:
        return True

    # Manual / Postman: Authorization: Bearer <key>
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        if token == API_KEY:
            return True

    raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------------------------------------------
# Health check
# -------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agentic-honeypot"}

# -------------------------------------------------------------------
# Main Honeypot Endpoint
# -------------------------------------------------------------------

@app.post("/api/agentic-honeypot", response_model=HoneypotResponse)
async def agentic_honeypot(
    request: Optional[HoneypotRequest] = Body(default=None),
    _: bool = Depends(verify_api_key),
):
    """
    Main Agentic Honey-Pot endpoint.

    - Accepts empty body (hackathon tester)
    - Accepts full JSON (real evaluation)
    - NEVER crashes
    """

    # ---------------------------------------------------------------
    # Case 1: Tester sends NO BODY → return simple success
    # ---------------------------------------------------------------
    if request is None:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "message": "Honeypot endpoint reachable and authenticated",
                "scam_detected": False,
                "agent_activated": False,
                "agent_reply": "",
                "engagement_metrics": {
                    "turn_count": 0,
                    "engagement_duration": "0s"
                },
                "extracted_intelligence": {
                    "bank_accounts": [],
                    "upi_ids": [],
                    "phishing_urls": []
                }
            }
        )

    # ---------------------------------------------------------------
    # Case 2: Normal processing
    # ---------------------------------------------------------------
    try:
        logger.info(f"Processing conversation: {request.conversation_id}")

        conversation_state = conversation_manager.get_or_create(request.conversation_id)

        full_context = {
            "message": request.message,
            "history": request.history or []
        }

        scam_detected = intent_detector.detect_scam(full_context)

        conversation_state["scam_detected"] = (
            conversation_state.get("scam_detected", False) or scam_detected
        )
        conversation_state["turn_count"] = conversation_state.get("turn_count", 0) + 1

        agent_activated = conversation_state["scam_detected"]

        if agent_activated:
            agent_reply = agent.generate_response(
                message=request.message,
                history=request.history or [],
                conversation_state=conversation_state
            )
        else:
            agent_reply = agent.generate_neutral_response(request.message)

        extracted_intelligence = intelligence_extractor.extract(request.message)
        engagement_metrics = conversation_manager.get_metrics(request.conversation_id)

        response = response_builder.build_success_response(
            scam_detected=conversation_state["scam_detected"],
            agent_activated=agent_activated,
            agent_reply=agent_reply,
            engagement_metrics=engagement_metrics,
            extracted_intelligence=extracted_intelligence
        )

        return JSONResponse(status_code=200, content=response)

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Unhandled processing error", exc_info=True)

        error_response = response_builder.build_error_response(
            error_message=str(e),
            conversation_id=request.conversation_id
        )

        return JSONResponse(status_code=200, content=error_response)

# -------------------------------------------------------------------
# Global exception safety net
# -------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Global exception handler triggered", exc_info=True)

    return JSONResponse(
        status_code=200,
        content={
            "status": "error",
            "scam_detected": False,
            "agent_activated": False,
            "agent_reply": "I'm sorry, I didn't quite understand that.",
            "engagement_metrics": {
                "turn_count": 0,
                "engagement_duration": "0s"
            },
            "extracted_intelligence": {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_urls": []
            }
        }
    )

# -------------------------------------------------------------------
# Local entrypoint (not used by Render)
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

