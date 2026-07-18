import { Injectable, BadRequestException } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { Inject } from '@nestjs/common';

export interface FixtureQuery {
  leagueId: string;
  seasonId?: string;
  matchday?: number;
  kickoffGte?: string;
  kickoffLte?: string;
}

@Injectable()
export class FixturesService {
  constructor(@Inject(PrismaClient) private prisma: PrismaClient) {}

  async findUpcoming(query: FixtureQuery) {
    if (!query.leagueId) throw new BadRequestException('leagueId is required');
    
    // Auto-select latest season if none provided
    let seasonId = query.seasonId;
    if (!seasonId) {
      const latestSeason = await this.prisma.season.findFirst({
        where: { leagueId: query.leagueId },
        orderBy: { name: 'desc' },
        select: { id: true },
      });
      seasonId = latestSeason?.id;
    }
    
    const where: any = {
      leagueId: query.leagueId,
      kickoff: { 
        gte: query.kickoffGte ? new Date(query.kickoffGte) : new Date(),
        ...(query.kickoffLte ? { lte: new Date(query.kickoffLte) } : {}),
      },
      status: { in: ['SCHEDULED', 'PENDING'] },
    };
    if (seasonId) where.seasonId = seasonId;
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
