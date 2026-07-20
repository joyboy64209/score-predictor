import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
});

export interface League {
  id: string;
  name: string;
  country: string | null;
  seasons: { id: string; name: string }[];
}

export interface Team {
  id: string;
  name: string;
  shortName: string | null;
}

export interface Prediction {
  id: string;
  market: string;
  selection: string;
  probability: number;
  confidence: number;
  expectedValue: number | null;
  reasons: { factors?: string[] } | null;
  modelVersion: string | null;
  createdAt: string;
}

export interface Fixture {
  id: string;
  matchday: number | null;
  kickoff: string;
  homeTeam: Team;
  awayTeam: Team;
  predictions: Prediction[];
}

export interface FixtureGroup {
  fixtureId: string;
  matchResult: Prediction[];
  doubleChance: Prediction[];
  combination: Prediction[];
  other: Prediction[];
}

export const leaguesApi = {
  list: () => api.get<League[]>('/leagues').then((r) => r.data),
};

export const fixturesApi = {
  upcoming: (leagueId: string, seasonId?: string, matchday?: number) => {
    const params = new URLSearchParams({ leagueId });
    if (seasonId) params.set('seasonId', seasonId);
    if (matchday !== undefined) params.set('matchday', String(matchday));
    return api.get<Fixture[]>('/fixtures', { params }).then((r) => r.data);
  },
  matchdays: (seasonId: string) =>
    api.get<number[]>('/fixtures/matchdays', { params: { seasonId } }).then((r) => r.data),
};

export const predictionsApi = {
  forFixture: (id: string) =>
    api.get<FixtureGroup | null>(`/predictions/fixture/${id}`).then((r) => r.data),
  thresholds: () =>
    api.get<Record<string, number>>('/predictions/thresholds').then((r) => r.data),
};
