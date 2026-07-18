# Match Predictor - Execution Guide

## Prerequisites Verification

Before starting, verify you have:
- [ ] Node.js 18+ (`node --version`)
- [ ] Python 3.9+ (`python --version`)
- [ ] PostgreSQL 14+ running on port 5432
- [ ] Git (optional, for cloning)

---

## Phase 1: Environment Setup (5 minutes)

### 1.1 Install Dependencies

**Backend:**
```bash
cd match-predictor/backend
npm install
```

**Frontend:**
```bash
cd match-predictor/frontend
npm install
```

**ML Service:**
```bash
cd match-predictor/ml
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

**Verify Kaggle CLI:**
```bash
kaggle --version
# Should output: Kaggle CLI version X.X.X
```

### 1.2 Verify API Keys

Check that `.env` file exists in `match-predictor/` with:
- `FOOTBALL_DATA_API_KEY` = 989739eec44a4228b8bec442a7b80cd4
- `API_FOOTBALL_API_KEY` = 8d3f8c67b7ee597d8df34deece065c9e
- `KAGGLE_USERNAME` = nahomdesta1000
- `KAGGLE_KEY` = cf5d27bb829eb9285ecd6bea0b45b8ba

---

## Phase 2: Database Setup (3 minutes)

### 2.1 Start PostgreSQL

**Windows:**
```bash
net start postgresql
```

**Verify it's running:**
```bash
pg_isready -U predictor
# Should output: localhost:5432 - accepting connections
```

### 2.2 Run Migrations

```bash
cd match-predictor/backend
npx prisma generate
npx prisma migrate dev --name init
npm run prisma:seed
```

**Expected output:**
- Prisma client generated
- Migration applied
- Seed complete (2 users, 1 league, 1 season, 8 teams, 5 fixtures, predictions)

### 2.3 Verify Database

```bash
# Optional: Open Prisma Studio to verify data
npx prisma studio
# Visit http://localhost:5555
```

---

## Phase 3: Start Services (3 terminals)

### Terminal 1 - Backend (Port 3001)

```bash
cd match-predictor/backend
npm run start:dev
```

**Expected output:**
```
[Nest] LOG NestJS successfully started
Backend listening on http://localhost:3001
```

**Verify:**
```bash
curl http://localhost:3001/api/leagues
# Should return JSON with leagues array
```

### Terminal 2 - ML Service (Port 8000)

```bash
cd match-predictor/ml
.venv\Scripts\activate  # Windows
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete
```

**Verify:**
```bash
curl http://localhost:8000/health
# Should return JSON with status and provider health
```

### Terminal 3 - Frontend (Port 3000)

```bash
cd match-predictor/frontend
npm run dev
```

**Expected output:**
```
VITE v5.4.8  ready in 500 ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

---

## Phase 4: System Verification (5 minutes)

### 4.1 Access Application

1. Open browser: http://localhost:3000
2. Login with: `admin@predictor.io` / `admin123`
3. You should see the Predictions page with seed data

### 4.2 Verify ML Service Health

1. Go to Admin Dashboard (http://localhost:3000/admin)
2. Check "ML Service" card shows "Online" with green checkmark
3. If "Offline", check ML service terminal for errors

### 4.3 Test Data Sync

1. In Admin Dashboard, click "Sync Fixtures Now"
2. Wait 30-60 seconds
3. Check ML service terminal for sync logs
4. Go back to Predictions page
5. Refresh - should see real fixtures from football-data.org

**Expected behavior:**
- Button shows "Syncing..." with spinner
- Success message appears
- New fixtures appear on predictions page

### 4.4 Verify Providers

Check ML service health endpoint:
```bash
curl http://localhost:8000/providers
```

**Expected output:**
```json
{
  "providers": {
    "football-data.org": true,
    "API-Football": true,
    "StatsBomb": false,  // OK if statsbombpy not installed
    "Understat": true,
    "Kaggle": true,
    "ClubElo": true
  }
}
```

---

## Phase 5: Initial Data Import (10-15 minutes)

### 5.1 Sync Competitions and Fixtures

**Option A: Via Admin Panel**
1. Go to Admin Dashboard
2. Click "Sync Fixtures Now"
3. Wait for completion

**Option B: Via API**
```bash
curl -X POST http://localhost:3001/admin/sync/fixtures \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected result:**
- 50-100+ fixtures imported for top leagues
- Teams, seasons, standings populated
- Check database: `SELECT COUNT(*) FROM "Fixture";`

### 5.2 Import Kaggle Historical Data

```bash
cd match-predictor/ml
.venv\Scripts\activate
python -c "from app.data_manager import data_manager; print(data_manager.import_historical(['English Premier League']))"
```

**Expected output:**
- Downloads datasets to `ml/datasets/kaggle/EPL/`
- Parses CSV files
- Returns list of historical fixtures

**Verify:**
```bash
dir ml\datasets\kaggle\EPL
# Should show downloaded CSV files
```

### 5.3 Sync Elo Ratings

```bash
curl http://localhost:8000/sync/elo -X POST
```

**Expected output:**
```json
{
  "status": "queued"
}
```

**Check database:**
```sql
SELECT COUNT(*) FROM "EloRating";
-- Should have 100+ teams
```

---

## Phase 6: Model Training (5-10 minutes)

### 6.1 Train Initial Model

**Option A: Via Admin Panel**
1. Go to Admin Dashboard
2. Click "Retrain Model"
3. Wait 5-10 minutes

**Option B: Via API**
```bash
curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{"modelName": "gradient_boosting", "competitions": ["English Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]}'
```

**Expected output:**
```json
{
  "modelVersion": "v20250116-123456",
  "algorithm": "gradient_boosting",
  "metrics": {
    "accuracy": 0.45,
    "precision": 0.44,
    "recall": 0.45,
    "f1": 0.44
  }
}
```

### 6.2 Verify Model

```bash
curl http://localhost:3001/admin/models \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected output:**
```json
[
  {
    "id": "xxx",
    "name": "gradient_boosting",
    "algorithm": "gradient_boosting",
    "metrics": {...},
    "trainedAt": "2025-01-16T12:34:56.000Z",
    "isActive": true
  }
]
```

---

## Phase 7: Test Predictions (2 minutes)

### 7.1 Generate Predictions

1. Go to Predictions page
2. Select a league with upcoming fixtures
3. Click on a fixture to expand
4. Should see predictions with confidence levels

**OR via API:**
```bash
curl http://localhost:3001/api/predictions/fixture/FIXTURE_ID
```

**Expected output:**
```json
{
  "fixtureId": "xxx",
  "matchResult": [
    {
      "market": "MATCH_RESULT",
      "selection": "HOME",
      "probability": 0.45,
      "confidence": 75.5,
      "expectedValue": 0.35,
      "status": "QUALIFIED",
      "reasons": {...}
    }
  ],
  "doubleChance": [...],
  "combination": [...],
  "other": [...]
}
```

---

## Phase 8: System Health Check

### 8.1 Run Comprehensive Health Check

```bash
curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "status": "ok",
  "timestamp": "2025-01-16T12:00:00Z",
  "providers": {
    "football-data.org": true,
    "API-Football": true,
    "StatsBomb": false,
    "Understat": true,
    "Kaggle": true,
    "ClubElo": true
  },
  "database": true,
  "model_present": true,
  "kaggle_datasets_present": true,
  "last_run": {
    "competitions": "2025-01-16T10:00:00Z",
    "elo": "2025-01-16T10:05:00Z"
  }
}
```

### 8.2 Verify Database Records

```sql
-- Connect to database
psql -U predictor -d match_predictor

-- Check records
SELECT 
  (SELECT COUNT(*) FROM "League") as leagues,
  (SELECT COUNT(*) FROM "Team") as teams,
  (SELECT COUNT(*) FROM "Fixture") as fixtures,
  (SELECT COUNT(*) FROM "Prediction") as predictions,
  (SELECT COUNT(*) FROM "EloRating") as elo_ratings,
  (SELECT COUNT(*) FROM "FeatureRow") as features;
```

**Expected minimums:**
- Leagues: 5+
- Teams: 100+
- Fixtures: 50+
- Elo Ratings: 100+
- Features: 100+ (if training completed)

---

## Troubleshooting

### Issue: PostgreSQL not connecting

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -U predictor

# If not, start it
net start postgresql

# Verify credentials in .env match PostgreSQL
# DATABASE_URL=postgresql://predictor:64209@localhost:5432/match_predictor
```

### Issue: ML service shows "down"

**Solution:**
```bash
# Check ML service terminal for errors
# Common issues:
# 1. Port 8000 already in use
# 2. Database connection failed
# 3. Missing dependencies

# Restart ML service
cd ml
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Issue: No fixtures showing

**Solution:**
1. Check if sync completed: Admin Dashboard → check for success message
2. Verify API keys in .env are valid
3. Check ML service logs for provider errors
4. Manually trigger sync via API

### Issue: Predictions not generating

**Solution:**
1. Ensure ML model is trained (Admin → Models section)
2. Check that fixtures have status "SCHEDULED" or "PENDING"
3. Verify predictions meet confidence thresholds
4. Check backend logs for ML service errors

### Issue: Kaggle download fails

**Solution:**
```bash
# Verify Kaggle CLI is installed
kaggle --version

# Verify credentials
dir C:\Users\HP\.kaggle\kaggle.json

# Test Kaggle API
kaggle datasets list

# If not configured, copy kaggle.json to ~/.kaggle/
```

---

## Performance Optimization

### For Production Use:

1. **Enable Request Caching:**
   - Already configured in `ml/app/http.py`
   - Reduces API calls to providers

2. **Schedule Background Sync:**
   - Scheduler runs every 6 hours by default
   - Syncs competitions, fixtures, standings, Elo

3. **Database Indexing:**
   - Prisma schema includes indexes on frequently queried fields
   - Monitor slow queries in production

4. **Model Retraining:**
   - Retrain weekly with new data
   - Use Admin panel or schedule via cron

---

## Next Steps After Setup

1. **Monitor Data Quality:**
   - Check predictions page regularly
   - Verify predictions are accurate
   - Adjust thresholds in Admin panel if needed

2. **Expand Coverage:**
   - Add more competitions via sync
   - Import more historical data
   - Experiment with different ML models

3. **Optimize Performance:**
   - Monitor API rate limits
   - Cache frequently accessed data
   - Optimize database queries

4. **Production Deployment:**
   - Use Docker Compose for deployment
   - Set up reverse proxy (nginx)
   - Configure SSL certificates
   - Set up monitoring and logging

---

## Success Criteria

✅ All services running without errors
✅ ML service health check shows "ok"
✅ At least 50 fixtures in database
✅ At least 100 Elo ratings synced
✅ At least 1 ML model trained
✅ Predictions page shows fixtures with predictions
✅ Predictions have confidence scores and expected values
✅ Admin panel can update thresholds
✅ Admin panel can trigger retrain

---

## Support

If you encounter issues:
1. Check the logs in each terminal
2. Verify all environment variables are set
3. Ensure PostgreSQL is running and accessible
4. Check API key validity
5. Review the SETUP.md file

The system is designed to be resilient - provider failures won't crash the application.