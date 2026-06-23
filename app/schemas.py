from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime, date
from uuid import UUID

class JobResponse(BaseModel):
    job_id: UUID

class JobStatusResponse(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    row_count_raw: Optional[int] = None
    row_count_clean: Optional[int] = None
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class JobSummarySchema(BaseModel):
    total_spend_inr: float
    total_spend_usd: float
    top_merchants: List[Dict[str, Any]]
    anomaly_count: int
    narrative: Optional[str]
    risk_level: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class TransactionSchema(BaseModel):
    txn_id: Optional[str]
    date: Optional[date]
    merchant: Optional[str]
    amount: Optional[float]
    currency: Optional[str]
    status: Optional[str]
    category: Optional[str]
    account_id: Optional[str]
    notes: Optional[str]
    is_anomaly: bool
    anomaly_reason: Optional[str]
    llm_category: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class JobResultsResponse(BaseModel):
    id: UUID
    status: str
    summary: Optional[JobSummarySchema]
    transactions: List[TransactionSchema]

class JobListResponse(BaseModel):
    jobs: List[JobStatusResponse]
