import { Global, Module } from '@nestjs/common';
import { ConfigStoreService } from './config-store.service';

@Global()
@Module({
  providers: [ConfigStoreService],
  exports: [ConfigStoreService],
})
export class ConfigStoreModule {}
