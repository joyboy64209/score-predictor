import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import axios, { AxiosInstance } from 'axios';

export interface MlPredictionRequest {
  fixtureId: string;
}

export interface MlPredictResponse {
  fixtureId: string;
  predictions: any[];
  modelVersion: string;
}

export interface MlTrainResponse {
  modelVersion: string;
  algorithm: string;
  metrics: any;
}

@Injectable()
export class MlService {
  private readonly logger = new Logger(MlService.name);
  private client: AxiosInstance;

  constructor() {
    const baseURL = process.env.ML_SERVICE_URL || 'http://localhost:8000';
    this.client = axios.create({ baseURL, timeout: 60000 });
  }

  async predict(fixtureId: string): Promise<MlPredictResponse> {
    try {
      const { data } = await this.client.post('/predict', { fixtureId });
      return data;
    } catch (err: any) {
      this.logger.error(`ML predict failed: ${err?.message}`);
      throw new InternalServerErrorException('ML service unavailable');
    }
  }

  async train(): Promise<MlTrainResponse> {
    try {
      const { data } = await this.client.post('/train', {});
      return data;
    } catch (err: any) {
      this.logger.error(`ML train failed: ${err?.message}`);
      throw new InternalServerErrorException('ML service unavailable');
    }
  }

  async health() {
    try {
      const { data } = await this.client.get('/health');
      return data;
    } catch {
      return { status: 'down' };
    }
  }
}
