# ML Pipeline & Data Providers

The ML service (`ml/`) ingests data from **multiple providers** through a
single unified interface (`DataManager`) and runs a modular feature-engineering
+ training pipeline.

## Architecture

```
ml/
  app/
    config.py            # env-driven settings (keys, timeouts, thresholds)
    schemas.py           # unified normalized schema (all entities)
    http.py              # retry + timeout + cache + graceful fallback
    providers/
      base_provider.py       # common interface
      football_data_provider.py
      api_football_provider.py
      statsbomb_provider.py
      understat_provider.py
      kaggle_provider.py
      clubelo_provider.py
    data_manager.py      # SINGLE entry point; orchestrates all providers
    feature_store.py     # configurable feature registry (53+ features)
    feature_pipeline.py  # builds MatchContexts, scaling, split, dataset version
    training.py          # scaling + CV + model/dataset versioning + persistence
    scheduler.py         # background sync jobs + health check
    db.py                # SQLAlchemy layer + idempotent init_db()
    persistence.py       # prediction persistence + threshold loading
    engine.py            # market/combination engine + thresholds + ranking
    main.py              # FastAPI (health, sync, train, predict)
    cli.py               # `python -m app.cli <cmd>`
  datasets/kaggle/<Competition>/
  migrations/001_provider_entities.sql
  verify_pipeline.py     # offline end-to-end verification
```

**Nothing in the app talks to a provider directly — only `DataManager`.**

## Providers

| Provider          | Purpose                                         | Auth |
| ----------------- | ----------------------------------------------- | ---- |
| football-data.org | Competitions, fixtures, teams, standings, results | `FOOTBALL_DATA_API_KEY` |
| API-Football      | Injuries, suspensions, lineups, team/player stats, odds | `API_FOOTBALL_API_KEY` |
| StatsBomb         | Historical event data (shots, passes, xG)       | open (statsbombpy) |
| Understat         | xG, xGA, xPoints, advanced attacking/defensive  | open (scraper) |
| Kaggle            | Historical datasets for training                | `KAGGLE_USERNAME`/`KAGGLE_KEY` |
| ClubElo           | Club Elo ratings (current + historical)         | open (CSV API) |

## Normalized schema
Competition, Season, Fixture, Team, Player, Venue, MatchStatistic,
PlayerStatistic, Standing, AdvancedMetric, Injury, Suspension, Lineup,
EventData, Odds, EloRating.

## Feature store (configurable)
Home/Away advantage, recent form, last 5/10 win %, goals scored/conceded,
goal difference, xG/xGA, shots, SOT, possession, pass accuracy, corners,
cards, Elo + Elo diff, league position, rest days, H2H, injury/suspension
score, attack/defense rating, momentum, BTTS %, over/under %, clean sheet %.
Add a feature by registering a `FeatureCalculator` — nothing else changes.

## Error handling
Every provider call goes through `http.request_json` (retry + timeout +
response cache) and `DataManager._safe` (catches exceptions, logs, returns
empty). Provider failures never crash the app.

## CLI
```
python -m app.cli health
python -m app.cli providers
python -m app.cli sync-elo
python -m app.cli sync-kaggle
python -m app.cli sync-competitions
python -m app.cli train --model gradient_boosting
python -m app.cli pipeline
```

## Database
New normalized tables are created idempotently by `db.init_db()` at service
startup, or manually via `ml/migrations/001_provider_entities.sql`. Mirrored
in `backend/prisma/schema.prisma`.
