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

  findOne(id: string) {
    return this.prisma.league.findUnique({
      where: { id },
      include: {
        seasons: { orderBy: { name: 'desc' }, select: { id: true, name: true } },
      },
    });
  }
}
