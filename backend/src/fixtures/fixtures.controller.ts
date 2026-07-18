import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { FixturesService } from './fixtures.service';

@ApiTags('fixtures')
@Controller('fixtures')
export class FixturesController {
  constructor(private fixtures: FixturesService) {}

  @Get()
  @ApiOperation({ summary: 'Upcoming fixtures filtered by league/season/matchday' })
  findUpcoming(
    @Query('leagueId') leagueId: string,
    @Query('seasonId') seasonId?: string,
    @Query('matchday') matchday?: string,
    @Query('kickoffGte') kickoffGte?: string,
    @Query('kickoffLte') kickoffLte?: string,
  ) {
    return this.fixtures.findUpcoming({
      leagueId,
      seasonId,
      matchday: matchday ? Number(matchday) : undefined,
      kickoffGte,
      kickoffLte,
    });
  }

  @Get('matchdays')
  @ApiOperation({ summary: 'Available matchdays for a season' })
  matchdays(@Query('seasonId') seasonId: string) {
    return this.fixtures.findMatchdays(seasonId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get a single fixture with its predictions' })
  findOne(@Param('id') id: string) {
    return this.fixtures.findOne(id);
  }
}
