import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
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

export interface AuthResponse {
  accessToken: string;
  user: { id: string; email: string; name: string; role: string };
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthResponse>('/auth/login', { email, password }).then((r) => r.data),
  register: (email: string, name: string, password: string) =>
    api.post<AuthResponse>('/auth/register', { email, name, password }).then((r) => r.data),
};

export const leaguesApi = {
  list: () => api.get<League[]>('/leagues').then((r) => r.data),
  distinct: () => api.get<League[]>('/leagues/distinct').then((r) => r.data),
};

export const fixturesApi = {
  upcoming: (leagueId: string, seasonId?: string, matchday?: number, kickoffGte?: string) => {
    const params = new URLSearchParams({ leagueId });
    if (seasonId) params.set('seasonId', seasonId);
    if (matchday !== undefined) params.set('matchday', String(matchday));
    if (kickoffGte) params.set('kickoffGte', kickoffGte);
    return api.get<Fixture[]>('/fixtures', { params }).then((r) => r.data);
  },
  upcomingFiltered: (params: { leagueId: string; matchday?: number; kickoffGte?: string; kickoffLte?: string }) => {
    const searchParams = new URLSearchParams({ leagueId: params.leagueId });
    if (params.matchday !== undefined) searchParams.set('matchday', String(params.matchday));
    if (params.kickoffGte) searchParams.set('kickoffGte', params.kickoffGte);
    if (params.kickoffLte) searchParams.set('kickoffLte', params.kickoffLte);
    return api.get<Fixture[]>('/fixtures', { params: searchParams }).then((r) => r.data);
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
