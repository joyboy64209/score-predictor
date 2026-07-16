import { Controller, Get, Param } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { LeaguesService } from './leagues.service';

@ApiTags('leagues')
@Controller('leagues')
export class LeaguesController {
  constructor(private leagues: LeaguesService) {}

  @Get()
  @ApiOperation({ summary: 'List leagues with their seasons' })
  findAll() {
    return this.leagues.findAll();
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get a league by id' })
  findOne(@Param('id') id: string) {
    return this.leagues.findOne(id);
  }
}
