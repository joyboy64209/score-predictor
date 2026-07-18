import { Injectable } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { Inject } from '@nestjs/common';

@Injectable()
export class LeaguesService {
  constructor(@Inject(PrismaClient) private prisma: PrismaClient) {}

  findAll() {
    return this.prisma.league.findMany({
      orderBy: { name: 'asc' },
      include: {
        seasons: { orderBy: { name: 'desc' }, select: { id: true, name: true } },
      },
    });
  }

  async findDistinct() {
    const leagues = await this.prisma.league.findMany({
      orderBy: { name: 'asc' },
      include: {
        seasons: { orderBy: { name: 'desc' }, select: { id: true, name: true } },
      },
    });

    // Deduplicate by name, keeping the first occurrence
    const seen = new Set<string>();
    return leagues.filter((league) => {
      if (seen.has(league.name)) {
        return false;
      }
      seen.add(league.name);
      return true;
    });
  }

  findOne(id: string) {
    return this.prisma.league.findUnique({
      where: { id },
      include: {
        seasons: { orderBy: { name: 'desc' }, select: { id: true, name: true } },
      },
    });
  }
}
