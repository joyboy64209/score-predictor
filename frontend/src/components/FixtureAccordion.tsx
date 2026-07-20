import { useState } from 'react';
import { Fixture, FixtureGroup } from '../api';
import { PredictionSection } from './PredictionCard';
import { useQuery } from '@tanstack/react-query';
import { predictionsApi } from '../api';
import { ChevronDown, Calendar, Target } from 'lucide-react';

function FixtureAccordion({ fixture }: { fixture: Fixture }) {
  const [open, setOpen] = useState(false);
  const { data: group } = useQuery<FixtureGroup | null>({
    queryKey: ['predictions', fixture.id],
    queryFn: () => predictionsApi.forFixture(fixture.id),
    enabled: open,
  });

  const qualifiedCount = fixture.predictions.length;
  const kickoff = new Date(fixture.kickoff);
  const dateStr = kickoff.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  const timeStr = kickoff.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="overflow-hidden rounded-2xl border border-white/80 bg-white/85 shadow-[0_10px_30px_rgba(15,23,42,0.08)] backdrop-blur transition-all hover:-translate-y-0.5 hover:shadow-[0_18px_50px_rgba(15,23,42,0.12)]">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-5 py-4 text-left transition-colors hover:bg-slate-50/70"
      >
        <div className="flex-1">
          <div className="mb-1 flex items-center gap-3">
            <span className="text-lg font-extrabold tracking-tight text-slate-950">{fixture.homeTeam.name}</span>
            <span className="rounded-full bg-brand-50 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.2em] text-brand-700">VS</span>
            <span className="text-lg font-extrabold tracking-tight text-slate-950">{fixture.awayTeam.name}</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" />
              {dateStr} at {timeStr}
            </span>
            {fixture.matchday && (
              <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                Matchday {fixture.matchday}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {qualifiedCount > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-3 py-1.5 text-xs font-bold text-white shadow-sm">
              <Target className="h-3.5 w-3.5" />
              {qualifiedCount} pick{qualifiedCount === 1 ? '' : 's'}
            </span>
          )}
          <ChevronDown
            className={`h-5 w-5 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`}
          />
        </div>
      </button>

      {open && (
        <div className="border-t border-slate-200 bg-slate-50 px-5 py-4">
          {!group ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent"></div>
              <span className="ml-3 text-sm text-slate-600">Loading predictions...</span>
            </div>
          ) : group.matchResult.length === 0 && group.doubleChance.length === 0 &&
            group.combination.length === 0 && group.other.length === 0 ? (
            <div className="py-6 text-center">
              <p className="text-sm text-slate-500">
                No high-confidence predictions available for this fixture.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <PredictionSection title="Match Result (1X2)" items={group.matchResult} />
              <PredictionSection title="Double Chance" items={group.doubleChance} />
              <PredictionSection title="Combination Bets" items={group.combination} />
              <PredictionSection title="Other Markets" items={group.other} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default FixtureAccordion;
