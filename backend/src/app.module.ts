import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';
import { LeaguesModule } from './leagues/leagues.module';
import { FixturesModule } from './fixtures/fixtures.module';
import { PredictionsModule } from './predictions/predictions.module';
import { MlModule } from './ml/ml.module';
import { AdminModule } from './admin/admin.module';
import { ConfigStoreModule } from './config-store/config-store.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    PrismaModule,
    ConfigStoreModule,
    UsersModule,
    AuthModule,
    LeaguesModule,
    FixturesModule,
    PredictionsModule,
    MlModule,
    AdminModule,
  ],
})
export class AppModule {}
