import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import AvatarUpload from '../components/profile/AvatarUpload'
import ProfileForm from '../components/profile/ProfileForm'
import ReviewCard from '../components/reviews/ReviewCard'
import RestaurantCard from '../components/restaurants/RestaurantCard'
import Spinner from '../components/ui/Spinner'
import { getMyReviews } from '../api/users'
import { getPreferences, updatePreferences } from '../api/users'
import { getMyFavorites } from '../api/users'
import { CUISINES, DIETARY, AMBIANCE, PRICE_RANGES, SORT_OPTIONS } from '../utils/constants'

function PreferencesTab() {
  const [prefs, setPrefs] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getPreferences()
      .then((res) => setPrefs(res.data))
      .catch(() => setPrefs({}))
  }, [])

  const toggle = (key, val) => {
    setPrefs((p) => {
      const arr = p[key] || []
      return {
        ...p,
        [key]: arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val],
      }
    })
  }

  const set = (key, val) => setPrefs((p) => ({ ...p, [key]: val }))

  const save = async () => {
    setSaving(true); setError('')
    try {
      const { data } = await updatePreferences({
        cuisine_preferences:  prefs.cuisine_preferences || [],
        dietary_restrictions: prefs.dietary_restrictions || [],
        ambiance_preferences: prefs.ambiance_preferences || [],
        price_range:          prefs.price_range || null,
        sort_preference:      prefs.sort_preference || 'rating',
        search_radius_miles:  prefs.search_radius_miles || 10,
      })
      setPrefs(data)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save.')
    } finally {
      setSaving(false)
    }
  }

  if (!prefs) return <div className="flex justify-center py-12"><Spinner /></div>

  return (
    <div className="space-y-8">
      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg">{error}</div>}

      {/* Cuisine */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Cuisine Preferences</h3>
        <div className="flex flex-wrap gap-2">
          {CUISINES.map((c) => (
            <button key={c} type="button" onClick={() => toggle('cuisine_preferences', c)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition
                ${(prefs.cuisine_preferences || []).includes(c)
                  ? 'bg-brand-600 text-white border-brand-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-brand-500'}`}>
              {c}
            </button>
          ))}
        </div>
      </section>

      {/* Dietary */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Dietary Restrictions</h3>
        <div className="flex flex-wrap gap-2">
          {DIETARY.map((d) => (
            <button key={d} type="button" onClick={() => toggle('dietary_restrictions', d)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition
                ${(prefs.dietary_restrictions || []).includes(d)
                  ? 'bg-green-600 text-white border-green-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-green-500'}`}>
              {d}
            </button>
          ))}
        </div>
      </section>

      {/* Ambiance */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Ambiance Preferences</h3>
        <div className="flex flex-wrap gap-2">
          {AMBIANCE.map((a) => (
            <button key={a} type="button" onClick={() => toggle('ambiance_preferences', a)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition
                ${(prefs.ambiance_preferences || []).includes(a)
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-purple-500'}`}>
              {a}
            </button>
          ))}
        </div>
      </section>

      {/* Price & Sort */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Price Range Preference</h3>
          <div className="space-y-2">
            {PRICE_RANGES.map((p) => (
              <label key={p.value} className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="price_range" value={p.value}
                  checked={prefs.price_range === p.value}
                  onChange={() => set('price_range', p.value)}
                  className="text-brand-600" />
                <span className="text-sm text-gray-600">{p.label}</span>
              </label>
            ))}
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="price_range" value=""
                checked={!prefs.price_range}
                onChange={() => set('price_range', null)}
                className="text-brand-600" />
              <span className="text-sm text-gray-600">No preference</span>
            </label>
          </div>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Default Sort</h3>
          <div className="space-y-2">
            {SORT_OPTIONS.map((s) => (
              <label key={s.value} className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="sort_preference" value={s.value}
                  checked={prefs.sort_preference === s.value}
                  onChange={() => set('sort_preference', s.value)}
                  className="text-brand-600" />
                <span className="text-sm text-gray-600">{s.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Search radius */}
      <div className="max-w-xs">
        <label className="block">
          <span className="text-sm font-semibold text-gray-700">Search Radius (miles)</span>
          <input type="number" min={1} max={100}
            value={prefs.search_radius_miles || 10}
            onChange={(e) => set('search_radius_miles', Number(e.target.value))}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
        </label>
      </div>

      <button onClick={save} disabled={saving}
        className="bg-brand-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-brand-700 disabled:opacity-60 transition">
        {saving ? 'Saving…' : saved ? 'Saved!' : 'Save Preferences'}
      </button>
    </div>
  )
}

function MyReviewsTab() {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMyReviews()
      .then((res) => setReviews(res.data.items))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>
  if (reviews.length === 0) return <p className="text-gray-400 text-sm">You haven't written any reviews yet.</p>

  return (
    <div className="space-y-1">
      {reviews.map((r) => (
        <ReviewCard key={r.id} review={r} restaurantId={r.restaurant_id}
          onUpdated={(updated) => setReviews((prev) => prev.map((x) => x.id === updated.id ? updated : x))}
          onDeleted={(id) => setReviews((prev) => prev.filter((x) => x.id !== id))}
        />
      ))}
    </div>
  )
}


function FavoritesTab() {
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMyFavorites()
      .then((res) => setFavorites(res.data.items || []))
      .finally(() => setLoading(false))
  }, [])

  // refresh favorites list when other parts of the app change favorites
  useEffect(() => {
    const handler = () => {
      setLoading(true)
      getMyFavorites()
        .then((res) => setFavorites(res.data.items || []))
        .finally(() => setLoading(false))
    }
    window.addEventListener('favorite:changed', handler)
    return () => window.removeEventListener('favorite:changed', handler)
  }, [])

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>
  if (!favorites || favorites.length === 0) return <p className="text-gray-400 text-sm">You have no favourites yet.</p>

  return (
    <div className="space-y-4">
      {favorites.map((r, idx) => (
        <RestaurantCard key={r.id} restaurant={r} index={idx} horizontal isFavorited />
      ))}
    </div>
  )
}

const TABS = [
  { id: 'info',        label: 'Profile Info' },
  { id: 'preferences', label: 'Preferences' },
  { id: 'reviews',     label: 'My Reviews' },
  { id: 'favorites',   label: 'Favourites' },
]

export default function ProfilePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { tab: tabParam } = useParams()
  const activeTab = tabParam || 'info'

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
        {/* Profile header */}
        <div className="bg-gradient-to-r from-brand-600 to-brand-700 px-8 py-8 flex flex-col sm:flex-row items-center gap-6">
          <AvatarUpload />
          <div className="text-white text-center sm:text-left">
            <h1 className="text-2xl font-bold">{user?.name}</h1>
            <p className="text-brand-100 text-sm mt-0.5">{user?.email}</p>
            {user?.city && (
              <p className="text-brand-200 text-sm mt-1">
                {user.city}{user.state ? `, ${user.state}` : ''}{user.country ? ` · ${user.country}` : ''}
              </p>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-8">
          <nav className="flex gap-0 -mb-px">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => navigate(t.id === 'info' ? '/profile' : `/profile/${t.id}`)}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors
                  ${activeTab === t.id
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab content */}
        <div className="p-8">
          {activeTab === 'info'        && <ProfileForm />}
          {activeTab === 'preferences' && <PreferencesTab />}
          {activeTab === 'reviews'     && <MyReviewsTab />}
          {activeTab === 'favorites'   && <FavoritesTab />}
        </div>
      </div>
    </div>
  )
}
