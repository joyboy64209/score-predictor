import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('admin@predictor.io');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      if (mode === 'login') await login(email, password);
      else await register(email, name, password);
      navigate('/');
    } catch {
      setError('Authentication failed. Check credentials.');
    }
  };

  return (
    <div className="mx-auto mt-16 max-w-md rounded-xl bg-white p-8 shadow">
      <h1 className="mb-6 text-center text-2xl font-bold text-brand-700">
        {mode === 'login' ? 'Sign in' : 'Create account'}
      </h1>
      <form onSubmit={submit} className="space-y-4">
        <input className="input" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)} type="email" required />
        {mode === 'register' && (
          <input className="input" placeholder="Name" value={name}
            onChange={(e) => setName(e.target.value)} required />
        )}
        <input className="input" placeholder="Password" type="password" value={password}
          onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="w-full rounded bg-brand-600 py-2 font-semibold text-white hover:bg-brand-700">
          {mode === 'login' ? 'Login' : 'Register'}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-500">
        {mode === 'login' ? "No account?" : 'Have an account?'}{' '}
        <button className="text-brand-600 underline"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? 'Register' : 'Login'}
        </button>
      </p>
    </div>
  );
}
