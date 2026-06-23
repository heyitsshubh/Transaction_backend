# AI-Powered Transaction Processing Pipeline

This repository contains the backend implementation for an asynchronous, AI-powered transaction processing pipeline. 

The system accepts raw, dirty CSV transaction exports, processes them asynchronously using a job queue, and leverages an LLM to categorize transactions and generate spending narratives.

## Tech Stack
- **API Framework**: FastAPI
- **Database**: PostgreSQL
- **Job Queue**: Celery + Redis
- **LLM**: Gemini-Flash-latest (via `google-generativeai`)
- **Containerization**: Docker & Docker Compose

---

## 🚀 Setup Instructions

The entire system—including the API, background worker, Redis, and PostgreSQL—is containerized and starts with a single command. **No manual installation of dependencies is required.**

### 1. Configure the Environment
Before starting the application, you must provide your Google Gemini API Key.
Create a `.env` file in the root of the repository:
```bash
touch .env
```
Add your API key to the `.env` file:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 2. Start the Application
Run the following command to build the images and start all services:
```bash
docker-compose up --build
```
*Note: The API will be exposed on port `8080` to prevent conflicts with local services, while the database and Redis instances are kept within the private Docker network.*

---

## ⚡ Example cURL Requests

Once the application is running, you can test the endpoints using the following `curl` commands. *(A sample `transactions.csv` is included in the root directory for your convenience).*

### 1. Upload a CSV File
Uploads the file, enqueues the background processing task, and immediately returns a Job ID.
```bash
curl -X 'POST' \
  'http://localhost:8080/jobs/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@transactions.csv;type=text/csv'
```
**Returns:** `{"job_id": "<UUID>"}`

### 2. Check Job Status
Replace `<UUID>` with the `job_id` returned from the upload step.
```bash
curl -X 'GET' \
  'http://localhost:8080/jobs/<UUID>/status' \
  -H 'accept: application/json'
```
**Returns:** Job metadata including status (`pending`, `processing`, `completed`, `failed`).

### 3. Fetch Job Results
Once the status is `completed`, use this endpoint to fetch the cleaned transactions, anomaly flags, and the LLM-generated narrative summary.
```bash
curl -X 'GET' \
  'http://localhost:8080/jobs/<UUID>/results' \
  -H 'accept: application/json'
```

### 4. List All Jobs
Fetch a list of all jobs processed by the system.
```bash
curl -X 'GET' \
  'http://localhost:8080/jobs' \
  -H 'accept: application/json'
```

*(Note: You can also explore and test all endpoints interactively via the built-in Swagger UI by navigating to `http://localhost:8080/docs` in your browser).*
