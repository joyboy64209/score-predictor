-- Migration: add normalized data-provider entities + feature store tables
-- Idempotent; safe to re-run. Mirrors backend/prisma/schema.prisma additions.

CREATE TABLE IF NOT EXISTS "Player" (
  "id" TEXT PRIMARY KEY,
  "name" TEXT NOT NULL,
  "teamId" TEXT,
  "externalId" TEXT,
  "position" TEXT,
  "createdAt" TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "Venue" (
  "id" TEXT PRIMARY KEY,
  "name" TEXT NOT NULL,
  "city" TEXT,
  "externalId" TEXT
);

CREATE TABLE IF NOT EXISTS "MatchStatistic" (
  "id" TEXT PRIMARY KEY,
  "fixtureId" TEXT,
  "homeShots" INTEGER,
  "awayShots" INTEGER,
  "homeShotsOnTarget" INTEGER,
  "awayShotsOnTarget" INTEGER,
  "homePossession" DOUBLE PRECISION,
  "awayPossession" DOUBLE PRECISION,
  "homePassAccuracy" DOUBLE PRECISION,
  "awayPassAccuracy" DOUBLE PRECISION,
  "homeCorners" INTEGER,
  "awayCorners" INTEGER,
  "homeYellow" INTEGER,
  "awayYellow" INTEGER,
  "homeRed" INTEGER,
  "awayRed" INTEGER,
  "homeXg" DOUBLE PRECISION,
  "awayXg" DOUBLE PRECISION,
  "homeXga" DOUBLE PRECISION,
  "awayXga" DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS "PlayerStatistic" (
  "id" TEXT PRIMARY KEY,
  "fixtureId" TEXT,
  "playerName" TEXT,
  "teamName" TEXT,
  "minutes" INTEGER,
  "goals" INTEGER NOT NULL DEFAULT 0,
  "assists" INTEGER NOT NULL DEFAULT 0,
  "rating" DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS "Standing" (
  "id" TEXT PRIMARY KEY,
  "competition" TEXT,
  "season" TEXT,
  "teamName" TEXT,
  "position" INTEGER,
  "played" INTEGER NOT NULL DEFAULT 0,
  "wins" INTEGER NOT NULL DEFAULT 0,
  "draws" INTEGER NOT NULL DEFAULT 0,
  "losses" INTEGER NOT NULL DEFAULT 0,
  "goalsFor" INTEGER NOT NULL DEFAULT 0,
  "goalsAgainst" INTEGER NOT NULL DEFAULT 0,
  "points" INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "AdvancedMetric" (
  "id" TEXT PRIMARY KEY,
  "teamName" TEXT,
  "season" TEXT,
  "xg" DOUBLE PRECISION,
  "xga" DOUBLE PRECISION,
  "xpts" DOUBLE PRECISION,
  "npxg" DOUBLE PRECISION,
  "npxga" DOUBLE PRECISION,
  "ppda" DOUBLE PRECISION,
  "deep" DOUBLE PRECISION,
  "sca" DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS "Injury" (
  "id" TEXT PRIMARY KEY,
  "teamName" TEXT,
  "playerName" TEXT,
  "reason" TEXT,
  "type" TEXT,
  "until" TEXT
);

CREATE TABLE IF NOT EXISTS "Suspension" (
  "id" TEXT PRIMARY KEY,
  "teamName" TEXT,
  "playerName" TEXT,
  "reason" TEXT,
  "until" TEXT
);

CREATE TABLE IF NOT EXISTS "Lineup" (
  "id" TEXT PRIMARY KEY,
  "fixtureId" TEXT,
  "teamName" TEXT,
  "formation" TEXT,
  "starting" JSONB,
  "substitutes" JSONB
);

CREATE TABLE IF NOT EXISTS "EventData" (
  "id" TEXT PRIMARY KEY,
  "fixtureId" TEXT,
  "eventType" TEXT,
  "teamName" TEXT,
  "playerName" TEXT,
  "minute" INTEGER,
  "x" DOUBLE PRECISION,
  "y" DOUBLE PRECISION,
  "endX" DOUBLE PRECISION,
  "endY" DOUBLE PRECISION,
  "extra" JSONB
);

CREATE TABLE IF NOT EXISTS "EloRating" (
  "id" TEXT PRIMARY KEY,
  "teamName" TEXT,
  "rating" DOUBLE PRECISION,
  "rank" INTEGER,
  "date" TEXT,
  "country" TEXT
);

CREATE TABLE IF NOT EXISTS "Odds" (
  "id" TEXT PRIMARY KEY,
  "fixtureId" TEXT,
  "bookmaker" TEXT,
  "home" DOUBLE PRECISION,
  "draw" DOUBLE PRECISION,
  "away" DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS "FeatureRow" (
  "id" TEXT PRIMARY KEY,
  "fixtureId" TEXT,
  "features" JSONB,
  "label" INTEGER,
  "datasetVersion" TEXT,
  "createdAt" TIMESTAMP NOT NULL DEFAULT now()
);

-- Ensure Config singleton row exists for thresholds
INSERT INTO "Config" (id, thresholds)
VALUES ('singleton', '{"MATCH_RESULT":70,"DOUBLE_CHANCE":90,"OTHER":80,"COMBINATION":80}')
ON CONFLICT (id) DO NOTHING;
