import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaguesApi, fixturesApi, Fixture } from '../api';
import FixtureAccordion from '../components/FixtureAccordion';
import { Loader2, AlertCircle, Trophy } from 'lucide-react';

export default function PredictionsPage() {
  const leagues = useQuery({ queryKey: ['leagues'], queryFn: leaguesApi.list });
  const [leagueId, setLeagueId] = useState('');
  const [seasonId, setSeasonId] = useState('');
  const [matchday, setMatchday] = useState<number | undefined>();

  useEffect(() => {
    if (leagues.data?.length && !leagueId) setLeagueId(leagues.data[0].id);
  }, [leagues.data, leagueId]);

  useEffect(() => {
    setSeasonId('');
    setMatchday(undefined);
  }, [leagueId]);

  const seasons = leagues.data?.find((l) => l.id === leagueId)?.seasons ?? [];

  const matchdays = useQuery({
    queryKey: ['matchdays', seasonId],
    queryFn: () => fixturesApi.matchdays(seasonId),
    enabled: !!seasonId,
  });

  const fixtures = useQuery<Fixture[]>({
    queryKey: ['fixtures', leagueId, seasonId, matchday],
    queryFn: () => fixturesApi.upcoming(leagueId, seasonId || undefined, matchday),
    enabled: !!leagueId,
  });

  const withPicks = (fixtures.data ?? []).filter((f) => f.predictions.length > 0);

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
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Season</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
              value={seasonId}
              onChange={(e) => setSeasonId(e.target.value)}
            >
              <option value="">All seasons</option>
              {seasons.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
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
