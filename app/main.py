import os
from fastapi import FastAPI
from .database import engine, Base
from .routers import jobs

# Create tables if not exists
Base.metadata.create_all(bind=engine)

# Ensure uploads dir exists
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="AI-Powered Transaction Processing Pipeline")

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Transaction Processing API"}
