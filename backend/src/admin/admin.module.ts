import { Module } from '@nestjs/common';
import { AdminController } from './admin.controller';
import { ConfigStoreModule } from '../config-store/config-store.module';
import { MlModule } from '../ml/ml.module';

@Module({
  imports: [ConfigStoreModule, MlModule],
  controllers: [AdminController],
})
export class AdminModule {}
