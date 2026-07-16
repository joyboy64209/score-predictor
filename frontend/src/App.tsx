import { Routes, Route, Navigate, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import PredictionsPage from './pages/PredictionsPage';
import AdminPage from './pages/AdminPage';

function Navbar() {
  const { user, logout } = useAuth();
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold text-brand-700">
          ⚽ Match Predictor
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {user?.role === 'ADMIN' && <Link to="/admin" className="text-slate-600 hover:text-brand-600">Admin</Link>}
          {user ? (
            <>
              <span className="text-slate-500">{user.name}</span>
              <button onClick={logout} className="rounded bg-slate-100 px-3 py-1 hover:bg-slate-200">
                Logout
              </button>
            </>
          ) : (
            <Link to="/login" className="rounded bg-brand-600 px-3 py-1 text-white hover:bg-brand-700">
              Login
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  const { user } = useAuth();
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" /> : <LoginPage />} />
          <Route path="/" element={user ? <PredictionsPage /> : <Navigate to="/login" />} />
          <Route
            path="/admin"
            element={user?.role === 'ADMIN' ? <AdminPage /> : <Navigate to="/" />}
          />
        </Routes>
      </main>
    </div>
  );
}
