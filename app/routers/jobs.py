import shutil
import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Job, Transaction, JobSummary
from ..schemas import JobResponse, JobStatusResponse, JobResultsResponse, JobListResponse, JobSummarySchema, TransactionSchema
from ..tasks import process_job

router = APIRouter()

@router.post("/upload", response_model=JobResponse)
def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    # Save file
    filepath = os.path.join("uploads", file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create Job record
    job = Job(filename=file.filename)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Trigger Celery Task
    process_job.delay(str(job.id))
    
    return {"job_id": job.id}

@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job

@router.get("/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Results not available. Job status is {job.status}")
        
    transactions = db.query(Transaction).filter(Transaction.job_id == job_id).all()
    summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
    
    return {
        "job_id": job.id,
        "status": job.status,
        "summary": summary,
        "transactions": transactions
    }

@router.get("", response_model=JobListResponse)
def list_jobs(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    jobs = query.all()
    return {"jobs": jobs}
