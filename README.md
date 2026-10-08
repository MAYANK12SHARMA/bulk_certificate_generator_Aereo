# Bulk Certificate Generator — Django REST Framework

A backend implementation of the Bulk Certificate Generator assignment.

The assignment asks the backend to accept a bulk generation request, validate recipient data, generate a certificate from one predefined template, track progress, continue when one certificate fails, and expose generated certificates for retrieval. This project implements those requirements with Django + Django REST Framework, Celery, Redis, ReportLab, and a relational database. 

## Architecture

```text
Client
  |
  | POST /api/jobs/
  v
Django REST API
  |
  | create GenerationJob + Certificate rows
  | enqueue background task
  v
Redis  <---->  Celery Worker
                  |
                  | one recipient at a time
                  v
           ReportLab PDF generator
                  |
                  v
             Media storage

Client <---- GET /api/jobs/{id}/
Client <---- GET /api/jobs/{id}/certificates/
Client <---- GET /api/certificates/{id}/download/
```

### Why background processing?

Bulk PDF generation is CPU/file I/O work and should not hold an HTTP request open. The API therefore returns `202 Accepted` after persisting the job and queueing the generation task. A job stores total, processed, successful, and failed counters so the client can poll progress. The assignment allows either synchronous or background processing; background processing is used here to make larger batches safer and more responsive.

### Failure isolation

Each recipient is processed inside its own `try/except`. If ReportLab or another generation step fails for one recipient, that certificate is marked `FAILED` with an error message and the next recipient is still processed. When the task finishes, the job becomes `COMPLETED` or `COMPLETED_WITH_ERRORS`.

## Project structure

```text
bulk_certificate_generator/
├── certificates/
│   ├── migrations/
│   ├── services/
│   │   └── certificate_generator.py
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_download.py
│   │   └── test_generator.py
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── tasks.py
│   ├── urls.py
│   └── views.py
├── config/
│   ├── celery.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── media/
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── requirements.txt
└── README.md
```

## Local setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Redis

The background worker uses Redis as the Celery broker. The easiest option is Docker:

```bash
docker run --name certificate-redis -p 6379:6379 redis:7-alpine
```

### 4. Configure environment

Copy `.env.example` to `.env` and adjust values when needed.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the API

```bash
python manage.py runserver
```

### 7. Start the Celery worker in a second terminal

```bash
celery -A config.celery worker --loglevel=INFO
```

## Docker setup

Docker Compose starts Django, PostgreSQL, and Redis together:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`.

## API

### Create a bulk generation job

`POST /api/jobs/`

Example request:

```json
{
  "event_name": "Django Workshop 2026",
  "certificate_title": "Certificate of Participation",
  "event_date": "2026-10-08",
  "issuer_name": "Open Learning Club",
  "issuer_title": "Program Director",
  "recipients": [
    {
      "name": "Alice Johnson",
      "email": "alice@example.com"
    },
    {
      "name": "Bob Singh",
      "email": "bob@example.com"
    }
  ]
}
```

Successful response: `202 Accepted`

```json
{
  "job_id": "<uuid>",
  "status": "PENDING",
  "message": "Certificate generation job accepted.",
  "task_id": "<celery-task-id>",
  "status_url": "http://localhost:8000/api/jobs/<uuid>/"
}
```

### Get job status and progress

`GET /api/jobs/{job_id}/`

The response includes:

- `total_recipients`
- `processed_count`
- `successful_count`
- `failed_count`
- `progress_percent`
- `status`
- the certificate-level results

Possible job statuses:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `COMPLETED_WITH_ERRORS`
- `FAILED`

### List certificates for a job

`GET /api/jobs/{job_id}/certificates/`

### Get one certificate

`GET /api/certificates/{certificate_id}/`

### Download one generated certificate

`GET /api/certificates/{certificate_id}/download/`

A completed certificate is returned as a PDF attachment.

## Validation rules

The create endpoint validates:

- event and issuer fields are non-empty
- each recipient has a non-empty name
- each recipient has a valid email address
- a job contains at least one recipient
- a job contains at most 1000 recipients
- recipient email addresses are unique within the job, case-insensitively

Malformed requests return `400 Bad Request` before a job is created.

## Certificate template

The project deliberately uses one fixed ReportLab template. There is no template editor or multiple-design support. Each generated PDF contains the recipient name, certificate title, event name, event date, issuer information, and a unique certificate number.

## Testing

Run:

```bash
python manage.py test
```

The tests cover the assignment's required areas:

- creating a generation job
- input validation
- certificate generation
- job status/progress
- individual certificate failure without stopping the job
- retrieving/download of generated certificates

## Interview discussion points

### Why Django REST Framework?

DRF gives serializers for request validation, API views, predictable HTTP responses, and an easy path to authentication/permissions if the product later requires them.

### Why one background task per job instead of one HTTP request per certificate?

The client submits one bulk request, satisfying the bulk-generation requirement. The server creates child certificate records and processes them in the worker, so the client does not need to coordinate hundreds of API calls.

### Why store certificate rows before generation?

This makes progress and failures persistent. A client can immediately see how many certificates are expected and later see exactly which recipients succeeded or failed.

### What would change at much larger scale?

For tens or hundreds of thousands of recipients, I would shard a job into smaller Celery tasks, use object storage such as S3 for PDFs, add pagination to certificate results, add authentication/rate limiting, and potentially generate a ZIP asynchronously rather than keeping many files on local disk.

## Notes

This is intentionally scoped to the assignment rather than a full SaaS product. Authentication, multi-template support, email delivery, ZIP packaging, and a frontend are outside the required scope.
