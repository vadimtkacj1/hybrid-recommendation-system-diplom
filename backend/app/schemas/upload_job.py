from typing import Optional
from pydantic import BaseModel


class UploadJobQueued(BaseModel):
    job_id: str


class UploadJobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    synced_count: Optional[int] = None
    total_count: Optional[int] = None
    profile_updated: Optional[bool] = None
    error: Optional[str] = None
