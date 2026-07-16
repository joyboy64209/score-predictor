# API Reference

Base URL: `http://localhost:3001/api` (Swagger UI at `/api/docs`).

## Authentication
All protected routes require `Authorization: Bearer <token>`.

### POST `/auth/login`
```json
{ "email": "admin@predictor.io", "password": "admin123" }
```
Returns `{ accessToken, user }`.

### POST `/auth/register`
```json
{ "email": "u@x.io", "name": "U", "password": "secret123" }
```

## Leagues
### GET `/leagues`
Returns leagues with nested seasons `[{ id, name, country, seasons: [{id, name}] }]`.

## Fixtures
### GET `/fixtures`
Query params: `leagueId` (required), `seasonId?`, `matchday?`.
Returns upcoming fixtures with their `QUALIFIED` predictions.

### GET `/fixtures/matchdays?seasonId=...`
Returns available matchday numbers.

### GET `/fixtures/:id`
Single fixture with qualified predictions.

## Predictions
### GET `/predictions/fixture/:id`
Ranked, sectioned predictions:
```json
{
  "fixtureId": "...",
  "matchResult": [ { market, selection, probability, confidence, expectedValue, reasons, modelVersion } ],
  "doubleChance": [ ... ],
  "combination": [ ... ],
  "other": [ ... ]
}
```

### GET `/predictions/thresholds`
Returns current configurable confidence thresholds.

## Admin (ADMIN role)
| Method | Path                    | Purpose              |
| ------ | ----------------------- | -------------------- |
| GET    | `/admin/thresholds`     | Read thresholds      |
| PUT    | `/admin/thresholds`     | Update thresholds    |
| POST   | `/admin/retrain`        | Trigger ML retrain   |
| GET    | `/admin/ml-health`      | ML service health    |
| GET    | `/admin/models`         | List model versions  |
| GET    | `/admin/metrics`        | Prediction metrics   |
| GET    | `/admin/users`          | List users           |
| POST   | `/admin/users/:id/role` | Set user role        |

## ML Service (`:8000`)
| Method | Path       | Body                | Purpose                |
| ------ | ---------- | ------------------- | ---------------------- |
| GET    | `/health`  | –                   | Liveness               |
| POST   | `/train`   | `{}`                | Train & persist model  |
| POST   | `/predict` | `{ fixtureId }`     | Generate predictions   |
