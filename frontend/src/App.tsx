import { Routes, Route, Navigate, Link } from 'react-router-dom';
import PredictionsPage from './pages/PredictionsPage';
import AdminPage from './pages/AdminPage';
import { BarChart3, ShieldCheck, Sparkles } from 'lucide-react';

function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-white/70 bg-white/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-sky-500 text-white shadow-lg shadow-brand-500/20">
            <Sparkles className="h-5 w-5" />
          </span>
          <span>
            <span className="block text-lg font-extrabold tracking-tight text-slate-950">Match Predictor</span>
            <span className="block text-xs text-slate-500">Live fixtures, thresholds, and model controls</span>
          </span>
        </Link>

        <nav className="flex items-center gap-2 text-sm">
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 font-semibold text-slate-700 shadow-sm transition hover:border-sky-200 hover:text-brand-700"
          >
            <BarChart3 className="h-4 w-4" />
            Predictions
          </Link>
          <Link
            to="/admin"
            className="inline-flex items-center gap-2 rounded-full bg-brand-600 px-3 py-2 font-semibold text-white shadow-lg shadow-brand-500/25 transition hover:bg-brand-700"
          >
            <ShieldCheck className="h-4 w-4" />
            Settings
          </Link>
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen text-slate-900">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute left-[-8rem] top-[-6rem] h-80 w-80 rounded-full bg-brand-500/10 blur-3xl" />
        <div className="absolute right-[-6rem] top-[12rem] h-96 w-96 rounded-full bg-sky-400/10 blur-3xl" />
      </div>
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<PredictionsPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </div>
  );
}
