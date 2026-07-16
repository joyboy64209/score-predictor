# ML Pipeline

The ML service (`ml/`) is a self-contained FastAPI app with a modular pipeline.

## Modules
- `config.py` — settings (DB url, thresholds, model dir).
- `providers.py` — `DataProvider` abstraction. Implementations:
  - `DbDataProvider` (default) reads fixtures/team stats from Postgres.
  - `CsvDataProvider` reads from CSV files (swap without touching logic).
- `pipeline.py` — `build_features`, `predict_1x2`, `train`, `load_model`.
- `engine.py` — derives the full market set + combination bets, applies
  configurable thresholds, ranks by confidence/expected value.
- `persistence.py` — writes predictions back to Postgres.
- `main.py` — FastAPI routes `/predict`, `/train`, `/health`.

## Market coverage
1X2, Double Chance (1X/X2/12), BTTS, Over/Under (0.5–4.5), Team Goals,
First Team to Score, Clean Sheets, Draw No Bet, Exact Score, Goal Ranges,
Half Winners, and 17 Combination Bets.

## Thresholds (configurable)
| Market            | Default |
| ----------------- | ------- |
| Match Result      | 70%     |
| Double Chance     | 90%     |
| Other Markets     | 80%     |
| Combination Bets  | 80%     |

## Flow
1. `POST /predict {fixtureId}` → load fixture + team stats.
2. `build_features` → feature vector.
3. `predict_1x2` → home/draw/away probabilities.
4. `derive_markets` expands to all markets; `derive_combinations` builds combos.
5. `qualify_and_rank` filters by thresholds, ranks.
6. `persist_predictions` stores results; backend reads them for the UI.
