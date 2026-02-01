# backend/routes/shadow_watch.py
"""
Shadow Watch API Routes
Week 4: Privacy controls, notifications, and library management
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from anchorgrid.core.dependencies import get_current_user
from anchorgrid.db.session import get_db
from anchorgrid.db.models import User
from anchorgrid.services.shadow_watch import (
    generate_library_snapshot,
    generate_recovery_file,
    calculate_trust_score,
    export_user_data,
    delete_user_data,
    undo_removal
)
from anchorgrid.core.logger import log
import json

router = APIRouter()


@router.get("/library")
async def get_library(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Shadow Watch library snapshot for current user
    
    Returns tiered library with scoring and fingerprint
    """
    try:
        snapshot = await generate_library_snapshot(current_user.id)
        log.info(f"📚 Library snapshot requested by user {current_user.id}")
        return snapshot
    except Exception as e:
        log.error(f"❌ Error generating library: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate library")


@router.post("/recovery")
async def create_recovery_file(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Shadow Watch recovery file
    
    Returns:
        - filename: str
        - content: dict (recovery data)
        - recovery_code: str (display once, user must save)
    
    ⚠️ Recovery code is shown ONLY ONCE
    """
    try:
        recovery_data = await generate_recovery_file(current_user.id)
        log.info(f"📥 Recovery file generated for user {current_user.id}")
        return {
            "filename": recovery_data["filename"],
            "recovery_code": recovery_data["recovery_code"],
            "message": "Save this recovery code securely. It will not be shown again.",
            "download_content": recovery_data["content"]
        }
    except Exception as e:
        log.error(f"❌ Error generating recovery file: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recovery file")


@router.post("/trust-score")
async def check_trust_score(
    request_context: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate trust score for current request
    
    Request body:
        {
            "ip": str,
            "user_agent": str,
            "library_fingerprint": str
        }
    
    Returns:
        {
            "trust_score": float,
            "risk_level": str,
            "action": str,
            "factors": dict
        }
    """
    try:
        trust_result = await calculate_trust_score(current_user.id, request_context)
        log.info(f"🔐 Trust score calculated for user {current_user.id}")
        return trust_result
    except Exception as e:
        log.error(f"❌ Error calculating trust score: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate trust score")


# === Privacy Controls (Week 4 COMPLETE) ===

@router.get("/privacy/export")
async def export_my_data(
    current_user: User = Depends(get_current_user)
):
    """
    Export all Shadow Watch data (GDPR compliance)
    
    Returns complete JSON export of:
    - Current library snapshot
    - All interests with scores
    - All activity events
    """
    try:
        export_data = await export_user_data(current_user.id)
        log.info(f"📥 Data exported for user {current_user.id}")
        
        # Return as downloadable JSON
        return Response(
            content=json.dumps(export_data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=shadow_watch_data_{current_user.username}.json"
            }
        )
    except Exception as e:
        log.error(f"❌ Error exporting data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data")


@router.delete("/privacy/delete")
async def delete_my_data(
    current_user: User = Depends(get_current_user),
    confirmation: str = None
):
    """
    Delete all Shadow Watch data (GDPR right to be forgotten)
    
    Query param:
        confirmation: Must be "DELETE_MY_DATA" to proceed
    
    ⚠️ WARNING: This is IRREVERSIBLE!
    """
    if confirmation != "DELETE_MY_DATA":
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Pass ?confirmation=DELETE_MY_DATA"
        )
    
    try:
        result = await delete_user_data(current_user.id)
        log.warning(f"🗑️ Data deleted for user {current_user.id}")
        return result
    except Exception as e:
        log.error(f"❌ Error deleting data: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete data")


@router.post("/undo/{undo_token}")
async def undo_library_removal(
    undo_token: str,
    current_user: User = Depends(get_current_user)
):
    """
    Restore a removed interest using undo token
    
    Token valid for 48 hours after removal notification
    """
    try:
        result = await undo_removal(undo_token)
        if result["success"]:
            log.info(f"🔄 Undo successful for user {current_user.id}")
        return result
    except Exception as e:
        log.error(f"❌ Error processing undo: {e}")
        raise HTTPException(status_code=500, detail="Failed to process undo")
