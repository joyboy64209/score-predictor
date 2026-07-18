import { Prediction } from '../api';
import { TrendingUp, Info } from 'lucide-react';

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
  const bgColor = value >= 80 ? 'bg-emerald-50' : value >= 70 ? 'bg-brand-50' : 'bg-amber-50';
  return (
    <div className={`h-2 w-full overflow-hidden rounded-full ${bgColor}`}>
      <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${Math.min(100, value)}%` }} />
    </div>
  );
}

export function PredictionRow({ p }: { p: Prediction }) {
  const evPositive = p.expectedValue !== null && p.expectedValue >= 0;
  
  return (
    <div className="group relative overflow-hidden rounded-lg border border-slate-200 bg-white p-4 transition-all hover:border-brand-300 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="mb-1 flex items-center gap-2">
            <span className="font-semibold text-slate-900">{selectionLabel(p.selection)}</span>
            {evPositive && (
              <span className="flex items-center gap-0.5 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                <TrendingUp className="h-3 w-3" />
                +EV
              </span>
            )}
          </div>
          <div className="mb-2">
            <ConfidenceBar value={p.confidence} />
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span className="font-medium">
              {(p.probability * 100).toFixed(1)}% probability
            </span>
            {p.expectedValue !== null && (
              <span className={`font-semibold ${evPositive ? 'text-emerald-600' : 'text-slate-600'}`}>
                EV: {evPositive ? '+' : ''}{p.expectedValue.toFixed(2)}
              </span>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-brand-600">{p.confidence.toFixed(0)}%</div>
          <div className="text-xs text-slate-500">confidence</div>
        </div>
      </div>
      
      {p.reasons?.factors && p.reasons.factors.length > 0 && (
        <details className="mt-3 group/details">
          <summary className="flex cursor-pointer items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700">
            <Info className="h-3.5 w-3.5" />
            View analysis
          </summary>
          <div className="mt-2 rounded-lg bg-slate-50 p-3">
            <ul className="space-y-1 text-xs text-slate-600">
              {p.reasons.factors.map((f, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-0.5 h-1 w-1 flex-shrink-0 rounded-full bg-brand-400" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
        </details>
      )}
    </div>
  );
}

export function PredictionSection({ title, items }: { title: string; items: Prediction[] }) {
  if (!items.length) return null;
  return (
    <div className="mb-5 last:mb-0">
      <h4 className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
        <span className="h-px flex-1 bg-slate-200" />
        {title}
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600">{items.length}</span>
        <span className="h-px flex-1 bg-slate-200" />
      </h4>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((p) => <PredictionRow key={p.id} p={p} />)}
      </div>
    </div>
  );
}
