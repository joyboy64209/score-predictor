import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaguesApi, fixturesApi, Fixture } from '../api';
import FixtureAccordion from '../components/FixtureAccordion';

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
    <div>
      <h1 className="mb-4 text-2xl font-bold">Upcoming Predictions</h1>

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <label className="text-sm">
          <span className="mb-1 block font-medium text-slate-600">League</span>
          <select className="input" value={leagueId}
            onChange={(e) => setLeagueId(e.target.value)} disabled={leagues.isLoading}>
            {leagues.data?.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-slate-600">Season</span>
          <select className="input" value={seasonId}
            onChange={(e) => setSeasonId(e.target.value)}>
            <option value="">All seasons</option>
            {seasons.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-slate-600">Matchday</span>
          <select className="input" value={matchday ?? ''}
            onChange={(e) => setMatchday(e.target.value ? Number(e.target.value) : undefined)}>
            <option value="">All matchdays</option>
            {matchdays.data?.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </label>
      </div>

      {fixtures.isLoading && <p className="text-slate-400">Loading fixtures…</p>}
      {fixtures.data && withPicks.length === 0 && (
        <p className="rounded bg-white p-6 text-center text-slate-500 shadow">
          No high-confidence predictions available for this selection.
        </p>
      )}
      <div className="space-y-3">
        {withPicks.map((f) => <FixtureAccordion key={f.id} fixture={f} />)}
      </div>
    </div>
  );
}
