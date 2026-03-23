import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    account_type: 'user',
    business_name: '',
    restaurant_location: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const updateField = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await signup(form)
      navigate(form.account_type === 'owner' ? '/owner' : '/')
    } catch (responseError) {
      setError(responseError.response?.data?.detail || 'Signup failed.')
    } finally {
      setLoading(false)
    }
  }

  const isOwner = form.account_type === 'owner'

  return (
    <div className="min-h-[calc(100vh-88px)] bg-[linear-gradient(180deg,#fff_0%,#fff5f5_100%)] px-4 py-10">
      <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
        <div>
          <p className="mb-4 inline-flex rounded-full bg-red-50 px-4 py-2 text-sm font-semibold text-red-600">Get started</p>
          <h1 className="text-5xl font-black tracking-tight text-gray-950">Create a reviewer or restaurant owner account.</h1>
          <p className="mt-4 text-lg text-gray-600">Owner accounts can claim restaurant listings and access analytics dashboards after logging in.</p>
        </div>

        <div className="rounded-[2rem] border border-gray-200 bg-white p-8 shadow-xl">
          <div className="mb-8 flex gap-2 rounded-2xl bg-gray-100 p-1">
            <button type="button" onClick={() => setForm((current) => ({ ...current, account_type: 'user' }))} className={`flex-1 rounded-2xl px-4 py-3 text-sm font-semibold ${!isOwner ? 'bg-white text-gray-950 shadow-sm' : 'text-gray-500'}`}>
              Reviewer
            </button>
            <button type="button" onClick={() => setForm((current) => ({ ...current, account_type: 'owner' }))} className={`flex-1 rounded-2xl px-4 py-3 text-sm font-semibold ${isOwner ? 'bg-white text-gray-950 shadow-sm' : 'text-gray-500'}`}>
              Owner
            </button>
          </div>

          {error && <div className="mb-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

          <form onSubmit={submit} className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Full name</span>
              <input name="name" value={form.name} onChange={updateField} required className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Email</span>
              <input name="email" type="email" value={form.email} onChange={updateField} required className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Password</span>
              <input name="password" type="password" minLength={6} value={form.password} onChange={updateField} required className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>

            {isOwner && (
              <>
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-gray-700">Business name</span>
                  <input name="business_name" value={form.business_name} onChange={updateField} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-gray-700">Restaurant location</span>
                  <input name="restaurant_location" value={form.restaurant_location} onChange={updateField} placeholder="Union City, CA" className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
                </label>
              </>
            )}

            <button type="submit" disabled={loading} className="w-full rounded-2xl bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
              {loading ? 'Creating account…' : `Create ${isOwner ? 'Owner' : 'Reviewer'} Account`}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account? <Link to="/login" className="font-semibold text-red-600">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
