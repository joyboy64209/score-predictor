import { Body, Controller, Get, Post, Put, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { AuthGuard } from '@nestjs/passport';
import { Roles } from '../auth/roles.decorator';
import { ConfigStoreService, Thresholds } from '../config-store/config-store.service';
import { MlService } from '../ml/ml.service';
import { PrismaClient } from '@prisma/client';
import { Inject } from '@nestjs/common';

@ApiTags('admin')
@ApiBearerAuth()
@Controller('admin')
@UseGuards(AuthGuard('jwt'))
export class AdminController {
  constructor(
    private config: ConfigStoreService,
    private ml: MlService,
    @Inject(PrismaClient) private prisma: PrismaClient,
  ) {}

  @Get('thresholds')
  @ApiOperation({ summary: 'Read confidence thresholds' })
  getThresholds(): Promise<Thresholds> {
    return this.config.getThresholds();
  }

  @Put('thresholds')
  @Roles('ADMIN')
  @ApiOperation({ summary: 'Update configurable confidence thresholds' })
  setThresholds(@Body() body: Partial<Thresholds>): Promise<Thresholds> {
    return this.config.setThresholds(body);
  }

  @Post('retrain')
  @Roles('ADMIN')
  @ApiOperation({ summary: 'Trigger ML model retraining' })
  retrain() {
    return this.ml.train();
  }

  @Get('ml-health')
  @ApiOperation({ summary: 'ML service health' })
  mlHealth() {
    return this.ml.health();
  }

  @Get('models')
  @Roles('ADMIN')
  @ApiOperation({ summary: 'List trained model versions' })
  models() {
    return this.prisma.modelVersion.findMany({ orderBy: { trainedAt: 'desc' } });
  }

  @Get('metrics')
  @Roles('ADMIN')
  @ApiOperation({ summary: 'Aggregate prediction metrics' })
  async metrics() {
    const qualified = await this.prisma.prediction.count({ where: { status: 'QUALIFIED' } });
    const total = await this.prisma.prediction.count();
    const byMarket = await this.prisma.prediction.groupBy({
      by: ['market'],
      _count: { _all: true },
      where: { status: 'QUALIFIED' },
    });
    return { qualified, total, byMarket };
  }

  @Get('users')
  @Roles('ADMIN')
  @ApiOperation({ summary: 'List users' })
  users() {
    return this.prisma.user.findMany({
      select: { id: true, email: true, name: true, role: true, createdAt: true },
    });
  }

  @Post('users/:id/role')
  @Roles('ADMIN')
  @ApiOperation({ summary: 'Set a user role' })
  setRole(@Query('id') id: string, @Query('role') role: 'ADMIN' | 'USER') {
    return this.prisma.user.update({
      where: { id },
      data: { role },
      select: { id: true, email: true, name: true, role: true },
    });
  }

  @Post('sync/fixtures')
  @Roles('ADMIN')
  @ApiOperation({ summary: 'Sync fixtures from football data providers' })
  async syncFixtures() {
    try {
      const result = await this.ml.syncFixtures();
      return { status: 'success', message: 'Fixture sync initiated', data: result };
    } catch (error: any) {
      return { status: 'error', message: error.message };
    }
  }
}
