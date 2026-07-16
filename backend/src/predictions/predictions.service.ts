import { Injectable } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { Inject } from '@nestjs/common';
import { ConfigStoreService, Thresholds } from '../config-store/config-store.service';
import { MarketType } from '@prisma/client';

export interface PredictionView {
  id: string;
  market: MarketType;
  selection: string;
  probability: number;
  confidence: number;
  expectedValue: number | null;
  reasons: any;
  modelVersion: string | null;
  createdAt: Date;
}

export interface FixturePredictionGroup {
  fixtureId: string;
  matchResult: PredictionView[];
  doubleChance: PredictionView[];
  combination: PredictionView[];
  other: PredictionView[];
}

function sectionFor(market: MarketType, selection: string): keyof Omit<FixturePredictionGroup, 'fixtureId'> {
  if (market === 'MATCH_RESULT') return 'matchResult';
  if (market === 'DOUBLE_CHANCE') return 'doubleChance';
  if (market === 'COMBINATION') return 'combination';
  return 'other';
}

@Injectable()
export class PredictionsService {
  constructor(
    @Inject(PrismaClient) private prisma: PrismaClient,
    private config: ConfigStoreService,
  ) {}

  private rank(preds: PredictionView[]): PredictionView[] {
    return [...preds].sort((a, b) => {
      if (b.confidence !== a.confidence) return b.confidence - a.confidence;
      return (b.expectedValue ?? 0) - (a.expectedValue ?? 0);
    });
  }

  async getForFixture(fixtureId: string): Promise<FixturePredictionGroup | null> {
    const fixture = await this.prisma.fixture.findUnique({
      where: { id: fixtureId },
      include: { predictions: { where: { status: 'QUALIFIED' } } },
    });
    if (!fixture) return null;

    const group: FixturePredictionGroup = {
      fixtureId,
      matchResult: [],
      doubleChance: [],
      combination: [],
      other: [],
    };

    for (const p of fixture.predictions) {
      const view: PredictionView = {
        id: p.id,
        market: p.market,
        selection: p.selection,
        probability: p.probability,
        confidence: p.confidence,
        expectedValue: p.expectedValue,
        reasons: p.reasons,
        modelVersion: p.modelVersion,
        createdAt: p.createdAt,
      };
      group[sectionFor(p.market, p.selection)].push(view);
    }

    group.matchResult = this.rank(group.matchResult);
    group.doubleChance = this.rank(group.doubleChance);
    group.combination = this.rank(group.combination);
    group.other = this.rank(group.other);
    return group;
  }

  async getThresholds(): Promise<Thresholds> {
    return this.config.getThresholds();
  }
}
