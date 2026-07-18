import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  const passwordHash = await bcrypt.hash('admin123', 10);
  await prisma.user.upsert({
    where: { email: 'admin@predictor.io' },
    update: {},
    create: {
      email: 'admin@predictor.io',
      name: 'Admin',
      passwordHash,
      role: 'ADMIN',
    },
  });

  const passwordHash2 = await bcrypt.hash('user1234', 10);
  await prisma.user.upsert({
    where: { email: 'user@predictor.io' },
    update: {},
    create: {
      email: 'user@predictor.io',
      name: 'Demo User',
      passwordHash: passwordHash2,
      role: 'USER',
    },
  });

  const league = await prisma.league.upsert({
    where: { id: 'league-epl' },
    update: {},
    create: { id: 'league-epl', name: 'English Premier League', country: 'England', externalId: 'PL' },
  });

  const season = await prisma.season.upsert({
    where: { leagueId_name: { leagueId: league.id, name: '2025/2026' } },
    update: {},
    create: { leagueId: league.id, name: '2025/2026' },
  });

  const teamsData = [
    'Arsenal', 'Manchester City', 'Liverpool', 'Chelsea',
    'Manchester United', 'Tottenham', 'Newcastle', 'Aston Villa',
  ];
  const teams: Record<string, string> = {};
  for (const name of teamsData) {
    const t = await prisma.team.upsert({
      where: { id: `team-${name.toLowerCase().replace(/\s/g, '-')}` },
      update: {},
      create: { id: `team-${name.toLowerCase().replace(/\s/g, '-')}`, name, shortName: name.slice(0, 3).toUpperCase() },
    });
    teams[name] = t.id;
  }

  for (const [name, teamId] of Object.entries(teams)) {
    await prisma.teamSeasonStat.upsert({
      where: { id: `stat-${teamId}-${season.id}` },
      update: {},
      create: {
        id: `stat-${teamId}-${season.id}`,
        teamId,
        seasonId: season.id,
        played: 30,
        wins: Math.floor(Math.random() * 20) + 5,
        draws: Math.floor(Math.random() * 8),
        losses: Math.floor(Math.random() * 8),
        goalsFor: Math.floor(Math.random() * 40) + 30,
        goalsAgainst: Math.floor(Math.random() * 40) + 20,
      },
    });
  }

  const teamNames = Object.keys(teams);
  const now = new Date();
  for (let m = 1; m <= 5; m++) {
    const home = teamNames[(m - 1) % teamNames.length];
    const away = teamNames[m % teamNames.length];
    const kickoff = new Date(now.getTime() + m * 24 * 60 * 60 * 1000);
    const fixture = await prisma.fixture.upsert({
      where: { id: `fixture-seed-${m}` },
      update: {},
      create: {
        id: `fixture-seed-${m}`,
        externalId: `seed-${season.id}-${m}`,
        leagueId: league.id,
        seasonId: season.id,
        homeTeamId: teams[home],
        awayTeamId: teams[away],
        matchday: m,
        kickoff,
      },
    });

    const sample: Array<[any, string, number]> = [
      ['MATCH_RESULT', 'HOME', 0.45],
      ['MATCH_RESULT', 'DRAW', 0.27],
      ['MATCH_RESULT', 'AWAY', 0.28],
      ['DOUBLE_CHANCE', '1X', 0.72],
      ['DOUBLE_CHANCE', 'X2', 0.55],
      ['BTTS', 'YES', 0.61],
      ['OVER_UNDER', 'OVER_2_5', 0.58],
      ['COMBINATION', 'HOME_WIN_AND_OVER_2_5', 0.33],
    ];
    for (const [market, selection, probability] of sample) {
      const confidence = market === 'DOUBLE_CHANCE'
        ? probability * 100
        : probability * 100;
      await prisma.prediction.upsert({
        where: { id: `seed-pred-${fixture.id}-${selection}` },
        update: {},
        create: {
          id: `seed-pred-${fixture.id}-${selection}`,
          fixtureId: fixture.id,
          market,
          selection,
          probability,
          confidence,
          expectedValue: probability * 1.9 - 1,
          status: confidence >= 70 ? 'QUALIFIED' : 'REJECTED',
          reasons: { factors: ['Recent form', 'Home advantage', 'Head to head'] },
          modelVersion: 'v1-seed',
        },
      });
    }
  }

  // eslint-disable-next-line no-console
  console.log('Seed complete.');
}

main()
  .catch((e) => {
    // eslint-disable-next-line no-console
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
