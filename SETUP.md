# Match Predictor - Setup Guide

## Prerequisites

- Node.js 18+ and npm
- Python 3.9+ and pip
- PostgreSQL 14+ (running locally on port 5432)

## Quick Start

### 1. Install Dependencies

```bash
# Backend
cd backend
npm install

# Frontend
cd ../frontend
npm install

# ML Service
cd ../ml
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Database Setup

Make sure PostgreSQL is running with the credentials from `.env`:

```bash
# Start PostgreSQL service (Windows)
net start postgresql

# Or if using Docker:
docker run --name match-predictor-db -e POSTGRES_USER=predictor -e POSTGRES_PASSWORD=64209 -e POSTGRES_DB=match_predictor -p 5432:5432 -d postgres:16-alpine
```

Then run migrations and seed:

```bash
cd backend
npx prisma generate
npx prisma migrate dev --name init
npm run prisma:seed
```

### 3. Start Services

Open 3 terminal windows:

**Terminal 1 - Backend:**
```bash
cd backend
npm run start:dev
# Runs on http://localhost:3001
```

**Terminal 2 - ML Service:**
```bash
cd ml
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
uvicorn app.main:app --reload --port 8000
# Runs on http://localhost:8000
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:3001/api/docs (Swagger)
- **ML Service**: http://localhost:8000/docs (FastAPI docs)

### 5. Login

Use the demo credentials:
- **Admin**: admin@predictor.io / admin123
- **User**: user@predictor.io / user1234

## Fetch Real Fixture Data

1. Login as admin
2. Go to Admin Dashboard
3. Click "Sync Fixtures Now" to fetch upcoming matches from football-data.org
4. Wait for sync to complete (check browser console for progress)
5. Go back to home page to see fixtures with predictions

## Train ML Model

1. Ensure you have synced fixtures and have historical data
2. In Admin Dashboard, click "Retrain Model"
3. Wait for training to complete (may take several minutes)
4. The model will be saved and used for predictions

## Configuration

Edit `.env` file to customize:

- `THRESHOLD_MATCH_RESULT` - Minimum confidence for match result predictions (default: 70)
- `THRESHOLD_DOUBLE_CHANCE` - Minimum confidence for double chance (default: 90)
- `THRESHOLD_OTHER` - Minimum confidence for other markets (default: 80)
- `THRESHOLD_COMBINATION` - Minimum confidence for combinations (default: 80)

## API Keys

The following API keys are configured in `.env`:

- **FOOTBALL_DATA_API_KEY** - For fetching fixtures and standings
- **API_FOOTBALL_API_KEY** - For injuries, lineups, and additional data
- **KAGGLE_USERNAME/KEY** - For importing historical match data

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running: `pg_isready -U predictor`
- Check DATABASE_URL in `.env` matches your PostgreSQL credentials

### ML Service Not Responding
- Check if ML service is running on port 8000
- Verify ML_DATABASE_URL is correct
- Check ML service logs for errors

### No Fixtures Showing
- Click "Sync Fixtures Now" in admin panel
- Check browser console for sync progress
- Ensure API keys are valid in `.env`

### Predictions Not Generating
- Train the ML model first (Admin → Retrain Model)
- Ensure fixtures have been synced
- Check that predictions meet confidence thresholds

## Project Structure

```
match-predictor/
├── backend/          # NestJS API server
│   ├── src/
│   │   ├── auth/     # JWT authentication
│   │   ├── leagues/  # League management
│   │   ├── fixtures/ # Fixture queries
│   │   ├── predictions/ # Prediction logic
│   │   ├── ml/       # ML service client
│   │   ├── admin/    # Admin endpoints
│   │   └── config-store/ # Threshold management
│   └── prisma/       # Database schema & seed
├── frontend/         # React + Vite + Tailwind
│   └── src/
│       ├── pages/    # Login, Predictions, Admin
│       ├── components/ # FixtureAccordion, PredictionCard
│       └── api.ts    # API client
└── ml/               # FastAPI ML service
    └── app/
        ├── providers/ # Data providers (football-data, API-Football, etc.)
        ├── pipeline.py # Feature engineering
        ├── training.py # Model training
        ├── engine.py   # Prediction engine
        └── main.py     # FastAPI endpoints
```

## Next Steps

1. ✅ UI is polished and ready
2. ✅ API keys configured
3. ⏭️ Set up database and run migrations
4. ⏭️ Sync real fixtures from football-data.org
5. ⏭️ Train ML model with historical data
6. ⏭️ Test predictions on upcoming fixtures

## Support

For issues or questions, check the documentation in the `docs/` folder.