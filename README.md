# LinkedIn Automated Job Application App

This repository scaffolds a private FastAPI plus React project for tracking job applications and adding a LinkedIn automation module.

## Structure

- `app/`: FastAPI backend, SQLAlchemy models, security, and automation stubs
- `alembic/`: database migration setup and initial migration
- `frontend/`: React plus Vite dashboard with EN and DE translations
- `k8s/linkedin-app/`: AKS deployment manifests

## Backend setup

Run from the repository root:

```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

If you are using Azure Key Vault locally, authenticate first:

```zsh
az login
```

## Frontend setup

Run from `frontend/`:

```zsh
npm install
npm run dev
```

## Docker Compose setup

Run from the repository root:

```zsh
cat > .env <<'EOF'
APP_API_KEY=my-secret-key
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=
LINKEDIN_HEADLESS=true
EOF

docker compose up --build
```

Then open:

```text
http://localhost:5173
```

The backend API will be available at:

```text
http://localhost:8000
```

Useful Compose commands:

```zsh
docker compose up --build -d
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
docker compose down -v
```

## Example API calls

Run from the repository root in a second terminal:

```zsh
export APP_API_KEY=replace-with-long-random-string
curl http://127.0.0.1:8000/jobs -H "X-API-Key: $APP_API_KEY"
```

For PostgreSQL, use a SQLAlchemy URL like:

```zsh
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/linkedin_apply
```

```zsh
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $APP_API_KEY" \
  -d '{
    "job_title": "Backend Engineer",
    "company": "Example GmbH",
    "url": "https://www.linkedin.com/jobs/view/123456/",
    "status": "applied",
    "notes": "Manual seed",
    "platform": "LinkedIn"
  }'
```

```zsh
curl -X POST http://127.0.0.1:8000/automation/run -H "X-API-Key: $APP_API_KEY"
```

## Deployment

Apply manifests from the repository root:

```zsh
kubectl apply -f k8s/linkedin-app/
```

Replace placeholder image names, secrets, and Key Vault settings before deploying.

The automation implementation is in `app/automation/linkedin_bot.py`. It logs into LinkedIn, searches by configured keywords and location, attempts Easy Apply, and records each attempt in the database.

## Important

Automating LinkedIn applications may violate LinkedIn Terms of Service. Keep the deployment private, rate-limited, and manually supervised.
