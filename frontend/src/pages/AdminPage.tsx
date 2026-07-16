import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';

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
  });

  const [form, setForm] = useState<Record<string, number>>({});

  const saveThresholds = useMutation({
    mutationFn: (body: Record<string, number>) => api.put('/admin/thresholds', body).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['thresholds'] }),
  });

  const retrain = useMutation({
    mutationFn: () => api.post('/admin/retrain').then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['metrics'] }),
  });

  const current = { ...(thresholds.data || {}), ...form };

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Admin</h1>

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg bg-white p-4 shadow">
          <div className="text-xs uppercase text-slate-400">ML Service</div>
          <div className="mt-1 text-lg font-semibold">
            {mlHealth.data?.status === 'ok' ? '🟢 Online' : '🔴 Down'}
          </div>
        </div>
        <div className="rounded-lg bg-white p-4 shadow">
          <div className="text-xs uppercase text-slate-400">Qualified Picks</div>
          <div className="mt-1 text-lg font-semibold">{metrics.data?.qualified ?? '–'}</div>
        </div>
        <div className="rounded-lg bg-white p-4 shadow">
          <div className="text-xs uppercase text-slate-400">Total Predictions</div>
          <div className="mt-1 text-lg font-semibold">{metrics.data?.total ?? '–'}</div>
        </div>
      </div>

      <div className="mb-6 rounded-xl bg-white p-5 shadow">
        <h2 className="mb-3 font-semibold">Confidence Thresholds (%)</h2>
        <div className="grid gap-3 sm:grid-cols-4">
          {['MATCH_RESULT', 'DOUBLE_CHANCE', 'OTHER', 'COMBINATION'].map((k) => (
            <label key={k} className="text-sm">
              <span className="mb-1 block text-slate-500">{k.replace('_', ' ')}</span>
              <input type="number" className="input" value={current[k] ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, [k]: Number(e.target.value) }))} />
            </label>
          ))}
        </div>
        <button
          className="mt-4 rounded bg-brand-600 px-4 py-2 text-white hover:bg-brand-700 disabled:opacity-50"
          disabled={saveThresholds.isPending || Object.keys(form).length === 0}
          onClick={() => saveThresholds.mutate(form)}>
          {saveThresholds.isPending ? 'Saving…' : 'Save thresholds'}
        </button>
      </div>

      <div className="rounded-xl bg-white p-5 shadow">
        <h2 className="mb-3 font-semibold">Models</h2>
        <button
          className="rounded bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-50"
          disabled={retrain.isPending}
          onClick={() => retrain.mutate()}>
          {retrain.isPending ? 'Training…' : 'Retrain models'}
        </button>
        {retrain.data && (
          <p className="mt-3 text-sm text-slate-500">
            Trained <code>{retrain.data.modelVersion}</code> ({retrain.data.algorithm})
          </p>
        )}
      </div>
    </div>
  );
}
