"""
AI Router - Financial Intelligence API
======================================

Endpoints for multi-agent financial analysis.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from anchorgrid.api.deps import RequestContext, get_request_context
from anchorgrid.services.agent_service import agent_service


router = APIRouter()


class AIAnalysisRequest(BaseModel):
    """AI analysis request schema"""
    query: str = Field(..., description="Natural language financial query")
    include_reasoning: bool = Field(False, description="Whether to include specialized agent reasoning")


class AIAnalysisResponse(BaseModel):
    """AI analysis response schema"""
    status: str
    query: str
    symbols: List[str]
    agent_types: List[str]
    summary: str
    signals: dict
    execution_time_ms: float
    timestamp: str
    reasoning: Optional[List[dict]] = None


@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_query(
    request: AIAnalysisRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> AIAnalysisResponse:
    """
    Process a financial query through the QuantForge Multi-Agent System.
    
    **Requires Authentication**
    
    This endpoint:
    1. Classifies the query (Market Analysis, Fundamental Research, or Risk Management).
    2. Incorporates conversation context (multi-turn).
    3. Fetches real-time data and technical indicators.
    4. Performs parallel agent-based reasoning.
    5. Returns a consensus summary with actionable signals.
    """
    # Use user_id from context for conversation tracking
    user_id = str(ctx.user.id) if ctx.user else "anonymous"
    
    result = await agent_service.analyze_query(
        user_id=user_id,
        query=request.query,
        include_reasoning=request.include_reasoning
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=500 if "failed" in result["message"] else 400,
            detail=result["message"]
        )
    
    return AIAnalysisResponse(**result)


@router.get("/context")
async def get_ai_context(
    ctx: RequestContext = Depends(get_request_context),
):
    """Get the current conversation context for the authenticated user"""
    user_id = str(ctx.user.id) if ctx.user else "anonymous"
    session_ctx = agent_service.orchestrator.get_or_create_context(user_id)
    
    return {
        "user_id": user_id,
        "symbols_mentioned": list(session_ctx.symbols_mentioned),
        "turns_count": len(session_ctx.history) // 2,
        "last_updated": session_ctx.history[-1]["timestamp"] if session_ctx.history else None
    }


@router.delete("/context")
async def clear_ai_context(
    ctx: RequestContext = Depends(get_request_context),
):
    """Clear the conversation context for the authenticated user"""
    user_id = str(ctx.user.id) if ctx.user else "anonymous"
    if user_id in agent_service.orchestrator.contexts:
        agent_service.orchestrator.contexts[user_id].clear()
        return {"status": "success", "message": "Context cleared"}
    return {"status": "success", "message": "No context found"}
