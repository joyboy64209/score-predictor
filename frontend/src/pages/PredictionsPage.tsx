import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaguesApi, fixturesApi, Fixture } from '../api';
import FixtureAccordion from '../components/FixtureAccordion';
import { AlertCircle, Trophy, Loader2, Filter, CalendarDays, Goal, BadgeInfo } from 'lucide-react';

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
    <div className="animate-fadeIn space-y-6">
      <section className="panel overflow-hidden px-6 py-6 sm:px-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.2em] text-brand-700">
              <BadgeInfo className="h-3.5 w-3.5" />
              Desktop mode
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-950 sm:text-4xl">Upcoming Predictions</h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600 sm:text-base">
              Browse upcoming fixtures, inspect high-confidence picks, and adjust the thresholds that control what appears in the app.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:w-[28rem]">
            <div className="panel-soft p-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <Trophy className="h-4 w-4 text-amber-500" />
                Fixtures
              </div>
              <div className="mt-2 text-2xl font-extrabold text-slate-950">{fixtures.data?.length ?? '—'}</div>
            </div>
            <div className="panel-soft p-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <Goal className="h-4 w-4 text-emerald-500" />
                Picks
              </div>
              <div className="mt-2 text-2xl font-extrabold text-slate-950">{withPicks.length}</div>
            </div>
            <div className="panel-soft p-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <CalendarDays className="h-4 w-4 text-sky-500" />
                League
              </div>
              <div className="mt-2 truncate text-lg font-bold text-slate-950">{leagues.data?.find((l) => l.id === leagueId)?.name ?? 'Loading…'}</div>
            </div>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="panel px-6 py-5 sm:px-8">
        <div className="mb-4 flex items-center gap-2">
          <Filter className="h-5 w-5 text-brand-600" />
          <h2 className="text-lg font-bold text-slate-950">Filter Matches</h2>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">League</label>
            <select
              className="input"
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
              className="input"
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
              className="input"
              value={matchday ?? ''}
              onChange={(e) => setMatchday(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">All matchdays</option>
              {matchdays.data?.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        </div>
      </section>

      {/* Loading State */}
      {fixtures.isLoading && (
        <div className="flex flex-col items-center justify-center py-16">
          <Loader2 className="mb-4 h-12 w-12 animate-spin text-brand-600" />
          <p className="text-slate-600">Loading fixtures...</p>
        </div>
      )}

      {/* Empty State */}
      {!fixtures.isLoading && fixtures.data && withPicks.length === 0 && (
        <div className="panel px-12 py-14 text-center">
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
