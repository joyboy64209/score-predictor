import { Module } from '@nestjs/common';
import { PredictionsService } from './predictions.service';
import { PredictionsController } from './predictions.controller';
import { ConfigStoreModule } from '../config-store/config-store.module';

@Module({
  imports: [ConfigStoreModule],
  providers: [PredictionsService],
  controllers: [PredictionsController],
  exports: [PredictionsService],
})
export class PredictionsModule {}
