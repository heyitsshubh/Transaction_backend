# AI-Powered Transaction Processing Pipeline

This repository contains the backend implementation for an AI-Powered Transaction Processing Pipeline, built with FastAPI, PostgreSQL, Celery, Redis, and Gemini 1.5 Flash.

## Setup Instructions

1. Ensure you have Docker and Docker Compose installed.
2. Clone this repository.
3. Create a `.env` file in the root directory and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
4. Run the application:
   ```bash
   docker-compose up --build
   ```

## Example cURL Requests

### 1. Upload a CSV
```bash
curl -X POST http://localhost:8080/jobs/upload \
  -F "file=@transactions.csv"
```
*Returns:* `{"job_id": "uuid"}`

### 2. Check Status
```bash
curl http://localhost:8080/jobs/your_job_id/status
```

### 3. Get Results
```bash
curl http://localhost:8080/jobs/your_job_id/results
```

### 4. List Jobs
```bash
curl http://localhost:8080/jobs
```

## System Architecture

- **FastAPI**: Handles HTTP requests.
- **Celery + Redis**: Manages the asynchronous job queue for long-running data processing and LLM calls.
- **PostgreSQL**: Stores Job state, cleaned Transactions, and LLM Summaries.
