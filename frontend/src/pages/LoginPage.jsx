import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/'
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const updateField = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(form)
      navigate(from, { replace: true })
    } catch (responseError) {
      setError(responseError.response?.data?.detail || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-88px)] bg-[linear-gradient(180deg,#fff_0%,#fff5f5_100%)] px-4 py-10">
      <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
        <div>
          <p className="mb-4 inline-flex rounded-full bg-red-50 px-4 py-2 text-sm font-semibold text-red-600">Welcome back</p>
          <h1 className="text-5xl font-black tracking-tight text-gray-950">Log in to search, review, and manage restaurants.</h1>
          <p className="mt-4 text-lg text-gray-600">Reviewer accounts and restaurant owner accounts both use the same secure JWT login flow.</p>
        </div>

        <div className="rounded-[2rem] border border-gray-200 bg-white p-8 shadow-xl">
          <div className="mb-8">
            <Link to="/" className="text-3xl font-black text-red-600">yelp</Link>
            <p className="mt-2 text-sm text-gray-500">Sign in to continue</p>
          </div>

          {error && <div className="mb-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

          <form onSubmit={submit} className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Email</span>
              <input name="email" type="email" value={form.email} onChange={updateField} required className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Password</span>
              <input name="password" type="password" value={form.password} onChange={updateField} required className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>
            <button type="submit" disabled={loading} className="w-full rounded-2xl bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
              {loading ? 'Signing in…' : 'Log In'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Need an account? <Link to="/signup" className="font-semibold text-red-600">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
