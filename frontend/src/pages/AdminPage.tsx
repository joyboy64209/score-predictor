import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import { Activity, TrendingUp, Settings2, RefreshCw, CheckCircle2, XCircle, ShieldCheck, Sparkles } from 'lucide-react';

export default function AdminPage() {
  const qc = useQueryClient();
  const thresholds = useQuery({
    queryKey: ['thresholds'],
    queryFn: () => api.get<Record<string, number>>('/admin/thresholds').then((r) => r.data),
  });
  const metrics = useQuery({
    queryKey: ['metrics'],
    queryFn: () => api.get('/admin/metrics').then((r) => r.data),
  });
  const mlHealth = useQuery({
    queryKey: ['ml-health'],
    queryFn: () => api.get('/admin/ml-health').then((r) => r.data),
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
  });
  const models = useQuery({
    queryKey: ['models'],
    queryFn: () => api.get('/admin/models').then((r) => r.data),
  });

  const [form, setForm] = useState<Record<string, number>>({});

  const saveThresholds = useMutation({
    mutationFn: (body: Record<string, number>) => api.put('/admin/thresholds', body).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['thresholds'] });
      setForm({});
    },
  });

  const syncFixtures = useMutation({
    mutationFn: () => api.post('/admin/sync/fixtures').then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['fixtures'] }),
  });

  const retrain = useMutation({
    mutationFn: () => api.post('/admin/retrain').then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['metrics', 'models'] }),
  });

  const current = { ...(thresholds.data || {}), ...form };

  return (
    <div className="animate-fadeIn space-y-6">
      <section className="panel overflow-hidden px-6 py-6 sm:px-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-slate-900 px-3 py-1 text-xs font-bold uppercase tracking-[0.2em] text-white">
              <ShieldCheck className="h-3.5 w-3.5" />
              Admin controls
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-950">Settings</h1>
            <p className="mt-1 max-w-2xl text-sm text-slate-600">Manage thresholds, sync data, and retrain models from one place.</p>
          </div>
          <div className="inline-flex items-center gap-2 self-start rounded-full bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
            <Sparkles className="h-4 w-4" />
            Public access enabled
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="panel-soft p-5">
          <div className="flex items-center justify-between">
            <div className="text-xs uppercase tracking-wide text-slate-500">ML Service</div>
            {mlHealth.data?.status === 'ok' ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {mlHealth.data?.status === 'ok' ? 'Online' : 'Offline'}
          </div>
        </div>

        <div className="panel-soft p-5">
          <div className="flex items-center justify-between">
            <div className="text-xs uppercase tracking-wide text-slate-500">Qualified Picks</div>
            <TrendingUp className="h-5 w-5 text-brand-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{metrics.data?.qualified ?? '–'}</div>
        </div>

        <div className="panel-soft p-5">
          <div className="flex items-center justify-between">
            <div className="text-xs uppercase tracking-wide text-slate-500">Total Predictions</div>
            <Activity className="h-5 w-5 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{metrics.data?.total ?? '–'}</div>
        </div>

        <div className="panel-soft p-5">
          <div className="flex items-center justify-between">
            <div className="text-xs uppercase tracking-wide text-slate-500">Models</div>
            <Settings2 className="h-5 w-5 text-purple-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{models.data?.length ?? '–'}</div>
        </div>
      </div>

      {/* Thresholds Section */}
      <div className="panel px-6 py-6">
        <div className="mb-4 flex items-center gap-2">
          <Settings2 className="h-5 w-5 text-brand-600" />
          <h2 className="text-xl font-bold text-slate-900">Confidence Thresholds</h2>
        </div>
        <p className="mb-4 text-sm text-slate-600">
          Set minimum confidence levels for predictions to be displayed. Only predictions meeting these thresholds will be shown to users.
        </p>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { key: 'MATCH_RESULT', label: 'Match Result (1X2)', description: 'Home/Draw/Away' },
            { key: 'DOUBLE_CHANCE', label: 'Double Chance', description: '1X, X2, 12' },
            { key: 'OTHER', label: 'Other Markets', description: 'BTTS, Over/Under, etc.' },
            { key: 'COMBINATION', label: 'Combination Bets', description: 'Multiple markets' },
          ].map(({ key, label, description }) => (
            <div key={key} className="rounded-2xl border border-slate-200 bg-white/85 p-4 shadow-sm backdrop-blur">
              <label className="mb-2 block text-sm font-medium text-slate-700">{label}</label>
              <p className="mb-3 text-xs text-slate-500">{description}</p>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
                  value={current[key] ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: Number(e.target.value) }))}
                />
                <span className="absolute right-3 top-2 text-sm text-slate-500">%</span>
              </div>
            </div>
          ))}
        </div>

        <button
          className="mt-4 rounded-lg bg-brand-600 px-6 py-2.5 font-semibold text-white shadow-sm hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          disabled={saveThresholds.isPending || Object.keys(form).length === 0}
          onClick={() => saveThresholds.mutate(form)}>
          {saveThresholds.isPending ? (
            <span className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
              Saving...
            </span>
          ) : 'Save Thresholds'}
        </button>
      </div>

      {/* Data Sync Section */}
      <div className="panel px-6 py-6">
        <div className="mb-4 flex items-center gap-2">
          <RefreshCw className="h-5 w-5 text-blue-600" />
          <h2 className="text-xl font-bold text-slate-900">Data Synchronization</h2>
        </div>
        <p className="mb-4 text-sm text-slate-600">
          Fetch the latest fixtures and data from football data providers. This will update the database with upcoming matches.
        </p>

        <button
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          disabled={syncFixtures.isPending}
          onClick={() => syncFixtures.mutate()}>
          {syncFixtures.isPending ? (
            <span className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
              Syncing...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              Sync Fixtures Now
            </span>
          )}
        </button>
      </div>

      {/* Model Training Section */}
      <div className="panel px-6 py-6">
        <div className="mb-4 flex items-center gap-2">
          <RefreshCw className="h-5 w-5 text-emerald-600" />
          <h2 className="text-xl font-bold text-slate-900">Model Training</h2>
        </div>
        <p className="mb-4 text-sm text-slate-600">
          Retrain the ML model with the latest data. This process may take several minutes depending on the dataset size.
        </p>

        <button
          className="rounded-lg bg-emerald-600 px-6 py-2.5 font-semibold text-white shadow-sm hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          disabled={retrain.isPending}
          onClick={() => retrain.mutate()}>
          {retrain.isPending ? (
            <span className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
              Training Model...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              Retrain Model
            </span>
          )}
        </button>

        {retrain.data && (
          <div className="mt-4 rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800">
            <strong>Success!</strong> Trained model <code>{retrain.data.modelVersion}</code> using {retrain.data.algorithm}.
          </div>
        )}

        {/* Model History */}
        {models.data && models.data.length > 0 && (
          <div className="mt-6">
            <h3 className="mb-3 text-sm font-semibold text-slate-700">Recent Models</h3>
            <div className="space-y-2">
              {models.data.slice(0, 5).map((model: any) => (
                <div key={model.id} className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                  <div>
                    <div className="font-medium text-slate-900">{model.name}</div>
                    <div className="text-xs text-slate-500">{model.algorithm}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-500">
                      {new Date(model.trainedAt).toLocaleDateString()}
                    </div>
                    {model.isActive && (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                        Active
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
