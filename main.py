"""
Agentic Honey-Pot – AI Scam Engagement System
Final Stable FastAPI Entry Point (GUVI + Render + Postman compatible)
"""

import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.models import HoneypotRequest
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if not API_KEY:
    logger.warning("API_KEY environment variable not set! Authentication will fail.")

# -------------------------------------------------------------------
# Global in-memory components
# -------------------------------------------------------------------

conversation_manager = None
intent_detector = None
agent = None
intelligence_extractor = None
response_builder = None

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
# FastAPI App
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
    # GUVI tester
    if x_api_key and x_api_key == API_KEY:
        return True

    # Postman / manual testing
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        if token == API_KEY:
            return True

    raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------------------------------------------
# Health Endpoint
# -------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agentic-honeypot"}

# -------------------------------------------------------------------
# MAIN POST ENDPOINT (NO 422 GUARANTEED)
# -------------------------------------------------------------------

@app.post("/api/agentic-honeypot")
async def agentic_honeypot(
    request: Request,
    _: bool = Depends(verify_api_key),
):
    """
    Main honeypot endpoint.
    Accepts empty body (GUVI) and full JSON (real evaluation).
    """

    # Safely read JSON body
    try:
        body = await request.json()
    except Exception:
        body = None

    # ---------------- GUVI / Empty request ----------------
    if not body:
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

    # ---------------- Real processing ----------------
    try:
        honeypot_request = HoneypotRequest(**body)

        conversation_state = conversation_manager.get_or_create(
            honeypot_request.conversation_id
        )

        context = {
            "message": honeypot_request.message,
            "history": honeypot_request.history or []
        }

        scam_detected = intent_detector.detect_scam(context)

        conversation_state["scam_detected"] = (
            conversation_state.get("scam_detected", False) or scam_detected
        )
        conversation_state["turn_count"] = conversation_state.get("turn_count", 0) + 1

        agent_activated = conversation_state["scam_detected"]

        if agent_activated:
            agent_reply = agent.generate_response(
                message=honeypot_request.message,
                history=honeypot_request.history or [],
                conversation_state=conversation_state
            )
        else:
            agent_reply = agent.generate_neutral_response(
                honeypot_request.message
            )

        extracted_intelligence = intelligence_extractor.extract(
            honeypot_request.message
        )

        engagement_metrics = conversation_manager.get_metrics(
            honeypot_request.conversation_id
        )

        response = response_builder.build_success_response(
            scam_detected=conversation_state["scam_detected"],
            agent_activated=agent_activated,
            agent_reply=agent_reply,
            engagement_metrics=engagement_metrics,
            extracted_intelligence=extracted_intelligence
        )

        return JSONResponse(status_code=200, content=response)

    except Exception:
        logger.exception("Unhandled processing error")

        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "scam_detected": False,
                "agent_activated": False,
                "agent_reply": "Temporary issue. Please continue.",
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
# GET FALLBACK (GUVI COMPATIBILITY)
# -------------------------------------------------------------------

@app.get("/api/agentic-honeypot")
async def agentic_honeypot_get(
    _: bool = Depends(verify_api_key),
):
    return {
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

# -------------------------------------------------------------------
# Local execution (Render ignores this)
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
