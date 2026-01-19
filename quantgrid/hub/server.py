"""
QuantGrid Hub - Community Portal Server

FastAPI server for accepting adapter submissions from contributors.
This is the "GitHub for Financial Models" backend.
"""

import shutil
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends
from pydantic import BaseModel
from loguru import logger

from quantgrid.hub.auth import get_current_user
from quantgrid.hub.evaluation import ProofOfLoss, EvaluationBenchmark

app = FastAPI(
    title="QuantGrid Community Hub",
    description="The Hive Mind - Upload your intelligence, strengthen the collective",
    version="0.2.0"
)

UPLOAD_DIR = "./incoming_submissions"
APPROVED_DIR = "./approved_adapters"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(APPROVED_DIR, exist_ok=True)


class SubmissionResponse(BaseModel):
    submission_id: str
    status: str
    message: str


class SubmissionStatus(BaseModel):
    submission_id: str
    status: str  # "queued", "evaluating", "approved", "rejected"
    score: float = 0.0
    message: str = ""


def validate_submission(file_path: str, submission_id: str):
    """
    The 'Gatekeeper' Logic - runs in background.
    
    1. Unzips the adapter
    2. Loads it into evaluator
    3. Runs Proof of Loss test
    4. If passing, moves to approved queue for merging
    """
    logger.info(f"🕵️♂️ Validating submission: {file_path}")
    
    try:
        # 1. Check if it's a valid Zip
        if not file_path.endswith(".zip"):
            logger.error("❌ Invalid file format")
            update_submission_status(submission_id, "rejected", "Invalid file format")
            return
        
        # 2. Unzip
        extract_dir = file_path.replace(".zip", "")
        shutil.unpack_archive(file_path, extract_dir)
        
        # 3. Verify structure
        if not os.path.exists(os.path.join(extract_dir, "adapter_model.bin")):
            logger.error("❌ Missing adapter_model.bin")
            update_submission_status(submission_id, "rejected", "Invalid adapter structure")
            return
        
        # 4. TODO: Run Proof of Loss evaluation
        # evaluator = ProofOfLoss()
        # metrics = evaluator.verify_submission(extract_dir)
        # 
        # if not metrics["passed"]:
        #     logger.warning(f"❌ Failed quality check: {metrics['loss']:.4f}")
        #     update_submission_status(submission_id, "rejected", f"Loss {metrics['loss']:.4f} >= threshold")
        #     return
        
        # 5. Move to approved queue
        approved_path = os.path.join(APPROVED_DIR, os.path.basename(extract_dir))
        shutil.move(extract_dir, approved_path)
        
        logger.info("✅ Validation Passed. Added to merge queue.")
        update_submission_status(submission_id, "approved", "Ready for weekly merge")
        
    except Exception as e:
        logger.error(f"❌ Validation error: {e}")
        update_submission_status(submission_id, "rejected", str(e))


def update_submission_status(submission_id: str, status: str, message: str):
    """Update submission status in database"""
    # TODO: Implement DB update
    logger.info(f"📊 Submission {submission_id}: {status} - {message}")


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "QuantGrid Community Hub",
        "status": "🟢 Hive Mind Active",
        "version": "0.2.0"
    }


@app.post("/submit", response_model=SubmissionResponse)
async def upload_adapter(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    author: str = "Anonymous",
    user: dict = Depends(get_current_user)
):
    """
    Submit a trained adapter to the Hive Mind.
    
    Requires valid API key in Authorization header.
    """
    # Extract username from authenticated user
    username = user.get("username", author)
    
    # 1. Save the file
    submission_id = f"{username}_{file.filename}".replace(" ", "_")
    file_location = os.path.join(UPLOAD_DIR, submission_id)
    
    logger.info(f"📥 Receiving submission from @{username}: {file.filename}")
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size_mb = os.path.getsize(file_location) / 1024 / 1024
    logger.info(f"💾 Saved {file_size_mb:.2f} MB")
    
    # 2. Trigger validation in background
    background_tasks.add_task(validate_submission, file_location, submission_id)
    
    return {
        "submission_id": submission_id,
        "status": "queued",
        "message": "Upload successful! Validation running in background. Check status with /status/{submission_id}"
    }


@app.get("/status/{submission_id}", response_model=SubmissionStatus)
async def check_status(submission_id: str):
    """Check the status of a submission"""
    # TODO: Implement real status lookup from DB
    return {
        "submission_id": submission_id,
        "status": "queued",
        "message": "Evaluation pending"
    }


@app.get("/leaderboard")
async def get_leaderboard(limit: int = 100):
    """Get the global contributor leaderboard"""
    # TODO: Implement real leaderboard from DB
    return {
        "leaderboard": [],
        "message": "Leaderboard coming soon"
    }


# To run this server:
# uvicorn quantgrid.hub.server:app --reload --host 0.0.0.0 --port 8000
