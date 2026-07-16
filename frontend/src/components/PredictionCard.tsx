import { Prediction } from '../api';

const LABELS: Record<string, string> = {
  HOME: 'Home Win', DRAW: 'Draw', AWAY: 'Away Win',
  '1X': 'Home or Draw', 'X2': 'Draw or Away', '12': 'Home or Away',
  YES: 'Yes', NO: 'No',
};

export function selectionLabel(selection: string): string {
  return LABELS[selection] ?? selection.replace(/_/g, ' ');
}

export function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 80 ? 'bg-emerald-500' : value >= 70 ? 'bg-brand-500' : 'bg-amber-500';
  return (
    <div className="h-2 w-full overflow-hidden rounded bg-slate-100">
      <div className={`h-full ${color}`} style={{ width: `${Math.min(100, value)}%` }} />
    </div>
  );
}

export function PredictionRow({ p }: { p: Prediction }) {
  return (
    <div className="rounded-lg border bg-white p-3">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{selectionLabel(p.selection)}</span>
        <span className="font-semibold text-brand-700">{p.confidence.toFixed(1)}%</span>
      </div>
      <div className="mt-2">
        <ConfidenceBar value={p.confidence} />
      </div>
      <div className="mt-1 flex justify-between text-xs text-slate-400">
        <span>Prob {(p.probability * 100).toFixed(1)}%</span>
        {p.expectedValue !== null && (
          <span>EV {p.expectedValue >= 0 ? '+' : ''}{p.expectedValue.toFixed(2)}</span>
        )}
      </div>
      {p.reasons?.factors && (
        <details className="mt-2 text-xs text-slate-500">
          <summary className="cursor-pointer text-brand-600">Why?</summary>
          <ul className="mt-1 list-disc pl-4">
            {p.reasons.factors.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        </details>
      )}
    </div>
  );
}

export function PredictionSection({ title, items }: { title: string; items: Prediction[] }) {
  if (!items.length) return null;
  return (
    <div className="mb-4">
      <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">{title}</h4>
      <div className="grid gap-2 sm:grid-cols-2">
        {items.map((p) => <PredictionRow key={p.id} p={p} />)}
      </div>
    </div>
  );
}
