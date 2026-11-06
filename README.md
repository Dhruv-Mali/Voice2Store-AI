# Voice2Store AI

Voice2Store AI is an AI-powered voice-to-website platform designed for small retail shop owners who need a simple online presence without coding, design work, or content planning complexity.

## Problem statement

Small retail shop owners wanting basic online presence to display products, hours, and contact information cannot use complex website builders requiring coding knowledge, design skills, or content structure planning, and they need voice-to-website AI tools that convert natural speech descriptions into functional storefronts.

This creates a major gap in the market:

- Most local businesses are not technical and do not have time to build a website manually.
- Traditional website builders are too complex for non-technical users.
- Small business owners often describe their business in everyday speech, not in structured web content.
- They need a fast, guided, low-friction path to launch an online storefront.

## Severity and opportunity

- Severity Score: 9
- TAM Score: 90
- Whitespace Score: 7
- Frequency Score: 8.5
- ITCH Score: 92.4

These scores indicate a strong business problem with high urgency, clear demand, and a meaningful market opportunity for a simplified AI-powered website creation solution.

## Solution overview

Voice2Store AI helps shop owners describe their business in natural language, such as voice input or a short transcript, and turns that information into a complete, responsive storefront automatically.

The system:

- captures business voice input in English, Hindi, or Gujarati
- converts speech to structured business data
- generates a clean storefront layout with product, contact, and brand sections
- allows product management and website editing
- publishes the final storefront to a shareable web URL
- supports mobile-friendly public pages and business contact integrations

## Target users

- local grocery store owners
- small bakery and sweet shops
- clinics and service businesses
- fashion, electronics, home goods, and neighborhood retail stores
- business owners who need a website but do not want to code or design one

## Core user journey

1. A shop owner opens the dashboard.
2. They speak naturally about their business, products, and services.
3. The platform converts their voice into a structured store profile.
4. AI generates a professional storefront and product layout.
5. The owner can review, edit, and add products.
6. The storefront is published and shared online.

## Key features

### AI website generation
- voice-based business capture
- multilingual transcription support
- automatic website content generation
- ready-to-use storefront templates

### Product management
- add, edit, and delete products
- price and category management
- image uploads
- product visibility on the live website

### Live preview and editing
- website preview before publishing
- AI-assisted editing through natural language instructions
- immediate storefront updates

### Publishing and branding
- publish website with shareable URLs
- SEO-ready metadata
- WhatsApp contact integration
- QR code generation for store access

### SaaS monetization
- free, starter, and pro subscription plans
- secure payment verification with Razorpay
- subscription limits and usage tracking

## Technical architecture

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- responsive SaaS dashboard and storefront UI

### Backend
- Python FastAPI
- SQLAlchemy
- Pydantic
- JWT-based auth and ownership checks
- database-backed business and product management

### Data and services
- PostgreSQL for production data storage
- OpenAI speech-to-text integration
- secure Razorpay payment verification
- public storefront rendering independent from dashboard

## Why this matters

This product reduces the cost and complexity of getting online for local businesses. Instead of spending time learning website tools or hiring a developer, the shop owner can simply describe their business and let AI generate a working storefront.

It creates value by:

- increasing online presence for local businesses
- reducing time-to-launch from days to minutes
- eliminating technical barriers
- giving merchants confidence in digital sales and local discovery

## Business value

Voice2Store AI turns a common operational pain point into a clear SaaS opportunity:

- solves a real customer problem
- targets a large underserved SMB segment
- provides a simple and differentiated workflow
- supports recurring revenue through subscriptions and paid plans

## Project structure

- `frontend/` - Next.js dashboard and storefront UI
- `backend/` - FastAPI backend, auth, database logic, and AI flows
- `docker-compose.yml` - local containerized stack for frontend, backend, and Postgres
- `.env.example` - frontend shared environment template
- `backend/.env.example` - backend configuration template
- `docs/aws-production-deployment.md` - deployment playbook

## Quick start

### Frontend

```powershell
cd frontend
npm install
Copy-Item ..\.env.example .env.local
npm run dev
```

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Full stack with Docker

```powershell
docker compose up --build
```

Open the app in the browser:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

## Conclusion

Voice2Store AI is a practical AI-powered SaaS solution for small retail businesses that need a professional storefront without technical complexity. It replaces friction with voice-driven automation and gives local shop owners a simple path to digital visibility and online sales.
