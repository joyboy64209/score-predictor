import { Injectable, BadRequestException } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { Inject } from '@nestjs/common';

export interface FixtureQuery {
  leagueId: string;
  seasonId?: string;
  matchday?: number;
}

@Injectable()
export class FixturesService {
  constructor(@Inject(PrismaClient) private prisma: PrismaClient) {}

  async findUpcoming(query: FixtureQuery) {
    if (!query.leagueId) throw new BadRequestException('leagueId is required');
    const where: any = {
      leagueId: query.leagueId,
      kickoff: { gte: new Date() },
      status: { in: ['SCHEDULED', 'PENDING'] },
    };
    if (query.seasonId) where.seasonId = query.seasonId;
    if (query.matchday) where.matchday = query.matchday;

    return this.prisma.fixture.findMany({
      where,
      orderBy: { kickoff: 'asc' },
      include: {
        homeTeam: { select: { id: true, name: true, shortName: true } },
        awayTeam: { select: { id: true, name: true, shortName: true } },
        predictions: {
          where: { status: 'QUALIFIED' },
          orderBy: { confidence: 'desc' },
        },
      },
    });
  }

  async findMatchdays(seasonId: string) {
    const rows = await this.prisma.fixture.findMany({
      where: { seasonId, matchday: { not: null } },
      select: { matchday: true },
      distinct: ['matchday'],
      orderBy: { matchday: 'asc' },
    });
    return rows.map((r) => r.matchday).filter((m): m is number => m !== null);
  }

  async findOne(id: string) {
    return this.prisma.fixture.findUnique({
      where: { id },
      include: {
        homeTeam: { select: { id: true, name: true, shortName: true } },
        awayTeam: { select: { id: true, name: true, shortName: true } },
        predictions: { where: { status: 'QUALIFIED' }, orderBy: { confidence: 'desc' } },
      },
    });
  }
}
