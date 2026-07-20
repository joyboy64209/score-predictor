import { Routes, Route, Navigate, Link } from 'react-router-dom';
import PredictionsPage from './pages/PredictionsPage';
import AdminPage from './pages/AdminPage';

function Navbar() {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold text-brand-700">
          ⚽ Match Predictor
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/admin" className="text-slate-600 hover:text-brand-600">Settings</Link>
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/" element={<PredictionsPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </div>
  );
}
