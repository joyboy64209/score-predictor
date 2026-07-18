import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaguesApi, fixturesApi, Fixture } from '../api';
import FixtureAccordion from '../components/FixtureAccordion';
import { Loader2, AlertCircle, Trophy } from 'lucide-react';

type DateRange = '7' | '30' | 'all';

export default function PredictionsPage() {
  const leagues = useQuery({
    queryKey: ['leagues'],
    queryFn: leaguesApi.distinct,
  });

  const [leagueId, setLeagueId] = useState('');
  const [matchday, setMatchday] = useState<number | undefined>();
  const [dateRange, setDateRange] = useState<DateRange>('7');

  useEffect(() => {
    if (leagues.data?.length && !leagueId) setLeagueId(leagues.data[0].id);
  }, [leagues.data, leagueId]);

  useEffect(() => {
    setMatchday(undefined);
  }, [leagueId]);

  const selectedLeague = leagues.data?.find((l) => l.id === leagueId);
  const seasons = selectedLeague?.seasons ?? [];
  const latestSeasonId = seasons[0]?.id;

  const matchdays = useQuery({
    queryKey: ['matchdays', latestSeasonId],
    queryFn: () => {
      if (!latestSeasonId) throw new Error('No season available');
      return fixturesApi.matchdays(latestSeasonId);
    },
    enabled: !!latestSeasonId,
  });

  const fixtures = useQuery<Fixture[]>({
    queryKey: ['fixtures', leagueId, dateRange, matchday],
    queryFn: () => {
      const now = new Date();
      const params: { leagueId: string; matchday?: number; kickoffGte?: string; kickoffLte?: string } = {
        leagueId,
      };
      if (matchday !== undefined) params.matchday = matchday;
      if (dateRange === 'all') {
        params.kickoffGte = now.toISOString();
      } else {
        const days = Number(dateRange);
        const future = new Date(now);
        future.setDate(future.getDate() + days);
        params.kickoffGte = now.toISOString();
        params.kickoffLte = future.toISOString();
      }
      return fixturesApi.upcomingFiltered(params);
    },
    enabled: !!leagueId,
  });

  const withPicks = (fixtures.data ?? []).filter((f) => f.predictions.length > 0);

  // Error state
  if (leagues.error) {
    return (
      <div className="rounded-xl border-2 border-dashed border-red-300 bg-red-50 p-12 text-center">
        <AlertCircle className="mx-auto mb-4 h-12 w-12 text-red-400" />
        <h3 className="mb-2 text-lg font-semibold text-slate-900">Error Loading Leagues</h3>
        <p className="text-slate-600">{leagues.error.message || 'Failed to load leagues. Please try again later.'}</p>
      </div>
    );
  }

  // Loading state
  if (leagues.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="mb-4 h-12 w-12 animate-spin text-brand-600" />
        <p className="text-slate-600">Loading leagues...</p>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold text-slate-900">Upcoming Predictions</h1>
        <p className="text-slate-600">AI-powered football match predictions with high-confidence picks</p>
      </div>

      {/* Filters */}
      <div className="mb-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Filter Matches</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">League</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
              value={leagueId}
              onChange={(e) => setLeagueId(e.target.value)}
              disabled={leagues.isLoading}
            >
              {leagues.isLoading ? (
                <option>Loading leagues...</option>
              ) : (
                leagues.data?.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))
              )}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Date Range</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value as DateRange)}
            >
              <option value="7">Next 7 days</option>
              <option value="30">Next 30 days</option>
              <option value="all">All upcoming</option>
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Matchday</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
              value={matchday ?? ''}
              onChange={(e) => setMatchday(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">All matchdays</option>
              {matchdays.data?.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {fixtures.isLoading && (
        <div className="flex flex-col items-center justify-center py-16">
          <Loader2 className="mb-4 h-12 w-12 animate-spin text-brand-600" />
          <p className="text-slate-600">Loading fixtures...</p>
        </div>
      )}

      {/* Empty State */}
      {!fixtures.isLoading && fixtures.data && withPicks.length === 0 && (
        <div className="rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-12 text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-slate-400" />
          <h3 className="mb-2 text-lg font-semibold text-slate-900">No Predictions Available</h3>
          <p className="text-slate-600">
            No high-confidence predictions available for this selection. Try adjusting your filters or check back later.
          </p>
        </div>
      )}

      {/* Results */}
      {!fixtures.isLoading && withPicks.length > 0 && (
        <div>
          <div className="mb-4 flex items-center gap-2 text-sm text-slate-600">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <span>Found {withPicks.length} fixture{withPicks.length === 1 ? '' : 's'} with predictions</span>
          </div>
          <div className="space-y-3">
            {withPicks.map((f) => <FixtureAccordion key={f.id} fixture={f} />)}
          </div>
        </div>
      )}
    </div>
  );
}