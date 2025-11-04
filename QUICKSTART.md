# Quick Start Guide for Productionization

This guide walks you through the essential steps to productionize your Golfzon OCR application.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL database (local or cloud)
- Git repository
- Deployment platform account (Streamlit Cloud, AWS, GCP, etc.)

## Phase 1: Critical Setup (Week 1)

### Step 1: Environment Configuration

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Update `.env` with your production values:
   ```bash
   DATABASE_URL=postgresql://user:password@host:port/database
   ENVIRONMENT=production
   SECRET_KEY=<generate-a-secure-random-key>
   ```

3. Generate a secure secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

### Step 2: Database Migration

1. **Set up PostgreSQL database:**
   - Local: Use Docker Compose (`docker-compose up -d db`)
   - Cloud: Provision PostgreSQL on AWS RDS, Google Cloud SQL, or Azure Database

2. **Update database URL in `.env`:**
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. **Run migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

### Step 3: Docker Setup

1. **Build Docker image:**
   ```bash
   docker build -t golfzon-ocr .
   ```

2. **Test locally with Docker Compose:**
   ```bash
   docker-compose up
   ```

3. **Verify health check:**
   ```bash
   curl http://localhost:8501/_stcore/health
   ```

### Step 4: Security

1. **Add authentication** (choose one):
   - **Streamlit Cloud**: Uses built-in authentication
   - **Custom**: Implement authentication in `app.py`
   - **OAuth**: Add OAuth integration

2. **Remove secrets from code:**
   - ✅ Already done: Using environment variables
   - Ensure `.env` is in `.gitignore`

3. **Update `.gitignore`:**
   - ✅ Already updated to exclude `.env` files

### Step 5: CI/CD Setup

1. **Set up GitHub Actions:**
   - ✅ CI workflow already created (`.github/workflows/ci.yml`)
   - Push to trigger automated tests

2. **Configure secrets in GitHub:**
   - Go to Settings → Secrets → Actions
   - Add: `DOCKER_USERNAME`, `DOCKER_PASSWORD` (if using Docker Hub)

## Phase 2: Deployment (Week 2)

### Option A: Streamlit Cloud (Easiest)

1. **Push code to GitHub**

2. **Connect to Streamlit Cloud:**
   - Go to https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Select your repository

3. **Configure environment variables:**
   - Add all variables from `.env` file
   - Set up PostgreSQL connection string

4. **Deploy!**

### Option B: Docker Deployment

#### AWS ECS/Fargate

1. **Push image to ECR:**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   docker tag golfzon-ocr:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/golfzon-ocr:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/golfzon-ocr:latest
   ```

2. **Create ECS task definition**
3. **Create ECS service**
4. **Set up Application Load Balancer**

#### Google Cloud Run

1. **Build and push:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/golfzon-ocr
   ```

2. **Deploy:**
   ```bash
   gcloud run deploy golfzon-ocr \
     --image gcr.io/PROJECT_ID/golfzon-ocr \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

#### DigitalOcean App Platform

1. **Connect GitHub repository**
2. **Select Dockerfile**
3. **Configure environment variables**
4. **Deploy**

## Phase 3: Monitoring (Week 3)

### Step 1: Error Tracking

1. **Set up Sentry:**
   - Create account at https://sentry.io
   - Get DSN
   - Add to `.env`: `SENTRY_DSN=...`
   - Install: `poetry add sentry-sdk`
   - Add to `app.py`:
     ```python
     import sentry_sdk
     from sentry_sdk.integrations.streamlit import StreamlitIntegration
     sentry_sdk.init(
         dsn=config.SENTRY_DSN,
         integrations=[StreamlitIntegration()],
         traces_sample_rate=1.0,
     )
     ```

### Step 2: Logging

1. **Configure structured logging:**
   - Logs are already set up via config
   - Set `LOG_LEVEL` in environment
   - Connect to CloudWatch/Cloud Logging

### Step 3: Monitoring

1. **Health checks:**
   - ✅ Already implemented in `src/golfzon_ocr/health.py`
   - Set up uptime monitoring (Pingdom, UptimeRobot)

2. **Metrics:**
   - Set up CloudWatch/GCP Monitoring
   - Track: response times, error rates, database connections

## Phase 4: Performance Optimization (Week 4)

### Step 1: Database Optimization

1. **Add indexes:**
   ```sql
   CREATE INDEX idx_weekly_scores_league_week ON weekly_scores(league_id, week_number);
   CREATE INDEX idx_weekly_scores_player_week ON weekly_scores(player_id, week_number);
   ```

2. **Update models.py** to include indexes in Alembic migrations

### Step 2: Caching (Optional)

1. **Set up Redis:**
   - Add `REDIS_URL` to `.env`
   - Install: `poetry add redis`
   - Implement caching layer

### Step 3: Async Processing (Optional)

1. **Set up Celery for OCR:**
   - Install Celery + Redis
   - Move OCR processing to background tasks
   - Show progress updates

## Testing Checklist

Before going to production:

- [ ] All tests pass
- [ ] Database migrations work
- [ ] Health checks pass
- [ ] Authentication works
- [ ] File uploads work
- [ ] OCR processing works
- [ ] Database queries are optimized
- [ ] Error handling works
- [ ] Logging is configured
- [ ] Environment variables are set correctly
- [ ] Secrets are not in code
- [ ] Docker image builds successfully
- [ ] Application starts without errors

## Production Checklist

- [ ] Database backups configured
- [ ] Monitoring set up
- [ ] Error tracking configured
- [ ] Logging configured
- [ ] HTTPS enabled
- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] Rate limiting configured
- [ ] File size limits set
- [ ] Database connection pooling configured
- [ ] Health checks working
- [ ] Rollback plan documented

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql $DATABASE_URL

# Check connection from app
python -c "from golfzon_ocr.db import get_engine; engine = get_engine(); print(engine.connect())"
```

### Docker Build Issues

```bash
# Clean build
docker build --no-cache -t golfzon-ocr .

# Check logs
docker logs <container-id>
```

### Migration Issues

```bash
# Check current migration
poetry run alembic current

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head
```

## Next Steps

1. Review `PRODUCTIONIZATION.md` for detailed plan
2. Start with Phase 1 (Critical Setup)
3. Test thoroughly in staging
4. Deploy to production
5. Monitor and iterate

## Support

- Check logs: `docker logs <container-id>`
- Health check: `curl http://localhost:8501/_stcore/health`
- Database: Check connection string and credentials
- OCR: Verify Tesseract is installed in container

