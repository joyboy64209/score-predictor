import { Controller, Get, Param } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { PredictionsService } from './predictions.service';

@ApiTags('predictions')
@Controller('predictions')
export class PredictionsController {
  constructor(private predictions: PredictionsService) {}

  @Get('fixture/:id')
  @ApiOperation({ summary: 'Ranked, sectioned predictions for a fixture' })
  forFixture(@Param('id') id: string) {
    return this.predictions.getForFixture(id);
  }

  @Get('thresholds')
  @ApiOperation({ summary: 'Current confidence thresholds' })
  thresholds() {
    return this.predictions.getThresholds();
  }
}
