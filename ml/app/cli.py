"""CLI entrypoint for the data pipeline.

Usage:
  python -m app.cli health
  python -m app.cli sync-elo
  python -m app.cli sync-kaggle
  python -m app.cli train [--model gradient_boosting]
  python -m app.cli sync-competitions
  python -m app.cli pipeline        # full initial import + train + verify
"""

import argparse
import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cli")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .config import settings  # noqa: E402
from .data_manager import data_manager  # noqa: E402
from .scheduler import scheduler  # noqa: E402
from . import training  # noqa: E402
from . import db  # noqa: E402

TOP = ["English Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1", "UEFA Champions League"]


def cmd_health(args):
    print(json.dumps(scheduler.health_check(), indent=2))


def cmd_providers(args):
    print(json.dumps(data_manager.provider_status(), indent=2))


def cmd_sync_elo(args):
    print(json.dumps(scheduler.run_sync_elo(), indent=2))


def cmd_sync_kaggle(args):
    print(json.dumps(scheduler.run_import_kaggle(TOP), indent=2))


def cmd_sync_competitions(args):
    print(json.dumps(scheduler.run_sync_competitions(TOP), indent=2))


def cmd_train(args):
    res = scheduler.run_train(args.model, TOP)
    print(json.dumps(res, indent=2, default=str))


def cmd_pipeline(args):
    """Full initial import: kaggle -> features -> train -> verify predict."""
    logger.info("=== Initial data import pipeline ===")
    db.init_db()
    logger.info("Provider status: %s", data_manager.provider_status())
    fixtures = data_manager.import_historical(TOP)
    logger.info("Imported %d historical fixtures", len(fixtures))
    res = scheduler.run_train(args.model, TOP)
    logger.info("Training result: %s", res.get("modelVersion", res))
    # verify a prediction can be generated for a finished match
    if fixtures:
        from .providers import DbDataProvider
        from .pipeline import build_features
        from .engine import Threshold, derive_markets, derive_combinations, qualify_and_rank
        from .persistence import load_thresholds
        # Build features from the first historical fixture using its teams
        fx = fixtures[0]
        provider = DbDataProvider(settings.database_url)
        # Build a synthetic fixture id reference for prediction demo
        logger.info("Verifying feature build for sample fixture %s", fx.external_id)
        try:
            f, meta = build_features(provider, "demo")
            logger.info("Feature build OK: %s", list(meta.keys()))
        except Exception as exc:
            logger.warning("Prediction demo needs DB-backed fixtures: %s", exc)
    print(json.dumps(res, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Match Predictor data pipeline CLI")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("health").set_defaults(func=cmd_health)
    sub.add_parser("providers").set_defaults(func=cmd_providers)
    sub.add_parser("sync-elo").set_defaults(func=cmd_sync_elo)
    sub.add_parser("sync-kaggle").set_defaults(func=cmd_sync_kaggle)
    sub.add_parser("sync-competitions").set_defaults(func=cmd_sync_competitions)
    p_train = sub.add_parser("train")
    p_train.add_argument("--model", default="gradient_boosting")
    p_train.set_defaults(func=cmd_train)
    p_pipe = sub.add_parser("pipeline")
    p_pipe.add_argument("--model", default="gradient_boosting")
    p_pipe.set_defaults(func=cmd_pipeline)
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
