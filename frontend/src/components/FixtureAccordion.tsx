import { useState } from 'react';
import { Fixture, FixtureGroup } from '../api';
import { PredictionSection } from './PredictionCard';
import { useQuery } from '@tanstack/react-query';
import { predictionsApi } from '../api';

function FixtureAccordion({ fixture }: { fixture: Fixture }) {
  const [open, setOpen] = useState(false);
  const { data: group } = useQuery<FixtureGroup | null>({
    queryKey: ['predictions', fixture.id],
    queryFn: () => predictionsApi.forFixture(fixture.id),
    enabled: open,
  });

  const qualifiedCount = fixture.predictions.length;
  const kickoff = new Date(fixture.kickoff).toLocaleString();

  return (
    <div className="overflow-hidden rounded-xl border bg-white">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-slate-50"
      >
        <div>
          <div className="font-semibold">
            {fixture.homeTeam.name} <span className="text-slate-400">vs</span> {fixture.awayTeam.name}
          </div>
          <div className="text-xs text-slate-400">
            {kickoff}{fixture.matchday ? ` · Matchday ${fixture.matchday}` : ''}
          </div>
        </div>
        <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
          {qualifiedCount} pick{qualifiedCount === 1 ? '' : 's'}
        </span>
      </button>

      {open && (
        <div className="border-t px-4 py-4">
          {!group ? (
            <p className="text-sm text-slate-400">Loading…</p>
          ) : group.matchResult.length === 0 && group.doubleChance.length === 0 &&
            group.combination.length === 0 && group.other.length === 0 ? (
            <p className="text-sm text-slate-500">
              No high-confidence predictions available for this fixture.
            </p>
          ) : (
            <>
              <PredictionSection title="Match Result" items={group.matchResult} />
              <PredictionSection title="Double Chance" items={group.doubleChance} />
              <PredictionSection title="Combination Bets" items={group.combination} />
              <PredictionSection title="Other Markets" items={group.other} />
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default FixtureAccordion;
