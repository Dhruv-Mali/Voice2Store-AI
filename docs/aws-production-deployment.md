# AWS production deployment guide

This project is configured for a containerized deployment that can run on AWS ECS Fargate or Elastic Beanstalk. The recommended production setup is:

- Frontend: Next.js container behind an ALB or CloudFront distribution
- Backend: FastAPI container behind an ALB
- Database: Amazon RDS for PostgreSQL
- Object storage: S3 for uploaded media, generated files, or public assets
- Secrets: AWS Secrets Manager or SSM Parameter Store
- Logs: CloudWatch
- DNS: Route 53

## 1. Prepare AWS resources

1. Create an RDS PostgreSQL instance.
2. Create a VPC with private subnets for the database and public subnets for the ALB.
3. Create an ECS cluster and task definitions for the frontend and backend.
4. Set secrets for:
   - `JWT_SECRET_KEY`
   - `OPENAI_API_KEY`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `RAZORPAY_WEBHOOK_SECRET`
5. Configure environment variables in ECS task definitions or Secrets Manager.

## 2. Container configuration

Use the Dockerfiles in this repository:

- `backend/Dockerfile`
- `frontend/Dockerfile`

The backend runs Gunicorn with Uvicorn workers, which is a safer production choice than running bare `uvicorn` directly.

## 3. Database and environment

Set production values like:

```env
APP_ENV=production
DATABASE_URL=postgresql+psycopg://<user>:<password>@<rds-host>:5432/voice2store
FRONTEND_URL=https://app.example.com
CORS_ORIGINS=["https://app.example.com"]
ALLOWED_HOSTS=["app.example.com","api.example.com"]
JWT_SECRET_KEY=<secret>
LOG_LEVEL=INFO
```

## 4. Security checklist

- Force HTTPS at the load balancer or CloudFront layer.
- Disable Swagger/OpenAPI in production if you do not want public API docs.
- Restrict CORS to your domain list.
- Store secrets outside source control.
- Add CloudWatch log retention and structured logging.
- Turn on RDS backups and perform vulnerability scans.

## 5. Deployment commands

Build and test locally first:

```bash
docker compose build
docker compose up -d
```

Then push to AWS ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker build -t voice2store-backend ./backend
docker tag voice2store-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/voice2store-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/voice2store-backend:latest
```

Repeat for the frontend image.

## 6. Recommended production traffic pattern

- Route `/api` to the backend service.
- Route `/` and static content to the frontend app.
- Keep the API and frontend under the same domain or behind a trusted reverse proxy.
- Use CloudFront for global caching of public storefront pages.

## 7. Production hardening notes

- Use a dedicated Postgres user with least privilege.
- Set a constrained `ALLOWED_HOSTS` list.
- Add `Strict-Transport-Security`, `X-Frame-Options`, and `Content-Security-Policy` headers.
- Keep the public storefront secure while exposing only necessary routes.
