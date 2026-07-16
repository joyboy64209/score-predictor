import { Module } from '@nestjs/common';
import { FixturesService } from './fixtures.service';
import { FixturesController } from './fixtures.controller';
import { LeaguesModule } from '../leagues/leagues.module';

@Module({
  imports: [LeaguesModule],
  providers: [FixturesService],
  controllers: [FixturesController],
  exports: [FixturesService],
})
export class FixturesModule {}
