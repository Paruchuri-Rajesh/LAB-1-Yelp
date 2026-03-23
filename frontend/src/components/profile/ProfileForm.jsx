import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { updateMe } from '../../api/users'
import { GENDERS, COUNTRIES, LANGUAGES } from '../../utils/constants'

export default function ProfileForm() {
  const { user, refreshUser } = useAuth()
  const [form, setForm] = useState({
    name:     user?.name     || '',
    phone:    user?.phone    || '',
    about_me: user?.about_me || '',
    city:     user?.city     || '',
    state:    user?.state    || '',
    country:  user?.country  || '',
    languages: user?.languages || [],
    gender:   user?.gender   || '',
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved]   = useState(false)
  const [error, setError]   = useState('')

  const handle = (e) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: value }))
  }

  const toggleLanguage = (lang) => {
    setForm((f) => ({
      ...f,
      languages: f.languages.includes(lang)
        ? f.languages.filter((l) => l !== lang)
        : [...f.languages, lang],
    }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = { ...form }
      if (!payload.gender) delete payload.gender
      if (!payload.languages?.length) payload.languages = null
      const { data } = await updateMe(payload)
      refreshUser(data)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save changes.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-6">
      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg">{error}</div>}

      {/* Name */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Full Name</span>
          <input name="name" value={form.name} onChange={handle} required
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Phone Number</span>
          <input name="phone" value={form.phone} onChange={handle} type="tel"
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
        </label>
      </div>

      {/* About Me */}
      <label className="block">
        <span className="text-sm font-medium text-gray-700">About Me</span>
        <textarea name="about_me" value={form.about_me} onChange={handle} rows={3}
          className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
      </label>

      {/* Location */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">City</span>
          <input name="city" value={form.city} onChange={handle}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">State (Abbrev.)</span>
          <input name="state" value={form.state} onChange={handle} maxLength={10} placeholder="e.g. CA"
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Country</span>
          <select name="country" value={form.country} onChange={handle}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
            <option value="">Select country</option>
            {COUNTRIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </label>
      </div>

      {/* Gender */}
      <label className="block max-w-xs">
        <span className="text-sm font-medium text-gray-700">Gender</span>
        <select name="gender" value={form.gender} onChange={handle}
          className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
          <option value="">Prefer not to say</option>
          {GENDERS.map((g) => (
            <option key={g.value} value={g.value}>{g.label}</option>
          ))}
        </select>
      </label>

      {/* Languages */}
      <div>
        <span className="text-sm font-medium text-gray-700">Languages</span>
        <div className="mt-2 flex flex-wrap gap-2">
          {LANGUAGES.map((lang) => (
            <button
              key={lang} type="button"
              onClick={() => toggleLanguage(lang)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition
                ${form.languages.includes(lang)
                  ? 'bg-brand-600 text-white border-brand-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-brand-500'}`}
            >
              {lang}
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit" disabled={saving}
        className="bg-brand-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-brand-700 disabled:opacity-60 transition"
      >
        {saving ? 'Saving…' : saved ? 'Saved!' : 'Save Changes'}
      </button>
    </form>
  )
}
