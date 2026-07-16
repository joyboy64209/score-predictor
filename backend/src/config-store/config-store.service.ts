import { Injectable } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { Inject } from '@nestjs/common';

export interface Thresholds {
  MATCH_RESULT: number;
  DOUBLE_CHANCE: number;
  OTHER: number;
  COMBINATION: number;
}

const DEFAULT_THRESHOLDS: Thresholds = {
  MATCH_RESULT: Number(process.env.THRESHOLD_MATCH_RESULT ?? 70),
  DOUBLE_CHANCE: Number(process.env.THRESHOLD_DOUBLE_CHANCE ?? 90),
  OTHER: Number(process.env.THRESHOLD_OTHER ?? 80),
  COMBINATION: Number(process.env.THRESHOLD_COMBINATION ?? 80),
};

@Injectable()
export class ConfigStoreService {
  constructor(@Inject(PrismaClient) private prisma: PrismaClient) {}

  async getThresholds(): Promise<Thresholds> {
    const row = await this.prisma.config.findUnique({ where: { id: 'singleton' } });
    if (!row) return DEFAULT_THRESHOLDS;
    return { ...DEFAULT_THRESHOLDS, ...(row.thresholds as object) } as Thresholds;
  }

  async setThresholds(thresholds: Partial<Thresholds>): Promise<Thresholds> {
    const current = await this.getThresholds();
    const next = { ...current, ...thresholds };
    await this.prisma.config.upsert({
      where: { id: 'singleton' },
      create: { id: 'singleton', thresholds: next as object },
      update: { thresholds: next as object },
    });
    return next;
  }
}
