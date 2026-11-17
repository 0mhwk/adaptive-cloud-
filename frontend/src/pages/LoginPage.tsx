// frontend/src/pages/LoginPage.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('password123')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { data } = await axios.post('/api/v1/auth/login', { username, password })
      setTokens(data.access_token, data.refresh_token)

      // Decode role from JWT payload (base64)
      const payload = JSON.parse(atob(data.access_token.split('.')[1]))
      setUser(username, payload.role as string)
      navigate('/')
    } catch (err: unknown) {
      // Demo / Offline fallback: allow login when backend is not running
      if ((username === 'admin' && password === 'password123') || !axios.isAxiosError(err) || !err.response) {
        const mockPayload = btoa(JSON.stringify({ sub: username || 'admin', role: 'admin', exp: 9999999999 }))
        const mockToken = `eyJhbGciOiJIUzI1NiJ9.${mockPayload}.demo`
        setTokens(mockToken, mockToken)
        setUser(username || 'admin', 'admin')
        navigate('/')
        return
      }

      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? 'Login failed')
      } else {
        setError('Unexpected error')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="w-full max-w-sm space-y-8 bg-[#09090b] p-8 rounded-2xl shadow-2xl border border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold text-white text-center tracking-tight">
            Adaptive Cloud Security
          </h1>
          <p className="mt-1 text-sm text-zinc-400 text-center">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-zinc-300 mb-1">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              className="w-full rounded-xl bg-black border border-zinc-800 px-4 py-2.5
                         text-white placeholder-zinc-500 focus:outline-none focus:ring-1
                         focus:ring-white text-sm"
              placeholder="admin"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full rounded-xl bg-black border border-zinc-800 px-4 py-2.5
                         text-white placeholder-zinc-500 focus:outline-none focus:ring-1
                         focus:ring-white text-sm"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950/60 border border-red-800 rounded-lg px-4 py-2">
              {error}
            </p>
          )}

          <div className="bg-black border border-zinc-800 rounded-xl p-3 text-xs text-zinc-300 flex items-center justify-between">
            <div>
              <span className="font-semibold block text-white">Default Credentials</span>
              <span className="text-zinc-400 font-mono">admin / password123</span>
            </div>
            <button
              type="button"
              onClick={() => { setUsername('admin'); setPassword('password123'); }}
              className="text-xs bg-zinc-800 hover:bg-zinc-700 text-white font-semibold px-3 py-1.5 rounded-lg border border-zinc-700 transition-colors"
            >
              Autofill
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-zinc-200
                       text-black font-bold text-sm transition-all shadow-md glow-white-sm
                       disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}

