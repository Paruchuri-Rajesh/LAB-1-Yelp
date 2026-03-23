import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOwnerDashboard, getOwnedRestaurants } from '../api/owner'
import { importRestaurantsFromYelp } from '../api/restaurants'
import { useAuth } from '../contexts/AuthContext'
import Spinner from '../components/ui/Spinner'
import RestaurantCard from '../components/restaurants/RestaurantCard'

function StatCard({ label, value }) {
  return (
    <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-3 text-4xl font-black text-gray-950">{value}</p>
    </div>
  )
}

export default function OwnerDashboardPage() {
  const { user } = useAuth()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [syncForm, setSyncForm] = useState({ location: user?.city || 'Union City, CA', term: 'restaurants', limit: 25 })
  const [syncState, setSyncState] = useState({ loading: false, message: '', error: '' })

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const response = await getOwnerDashboard()
      setDashboard(response.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  const syncYelp = async (event) => {
    event.preventDefault()
    setSyncState({ loading: true, message: '', error: '' })
    try {
      const response = await importRestaurantsFromYelp({ ...syncForm, limit: Number(syncForm.limit) })
      setSyncState({ loading: false, message: response.data.message, error: '' })
      await loadDashboard()
    } catch (error) {
      setSyncState({ loading: false, message: '', error: error.response?.data?.detail || 'Yelp import failed.' })
    }
  }

  if (!user?.is_owner) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <h1 className="text-4xl font-black text-gray-950">Owner dashboard</h1>
        <p className="mt-4 text-gray-600">This page is only available to owner accounts.</p>
        <Link to="/signup" className="mt-6 inline-flex rounded-full bg-red-600 px-5 py-3 text-sm font-semibold text-white">Create owner account</Link>
      </div>
    )
  }

  if (loading) return <div className="flex justify-center py-24"><Spinner className="h-10 w-10" /></div>

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">Restaurant owner dashboard</p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-gray-950">Manage your restaurants and analytics.</h1>
        </div>
        <Link to="/search?location=Union%20City%2C%20CA" className="rounded-full border border-gray-300 px-5 py-3 text-sm font-semibold text-gray-900 hover:bg-gray-50">Browse restaurants to claim</Link>
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Claimed restaurants" value={dashboard?.total_restaurants || 0} />
        <StatCard label="Tracked views" value={dashboard?.total_views || 0} />
        <StatCard label="Total reviews" value={dashboard?.total_reviews || 0} />
        <StatCard label="Average rating" value={dashboard?.avg_rating || 0} />
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[0.92fr_1.08fr]">
        <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-bold text-gray-950">Import from Yelp</h2>
          <p className="mt-2 text-sm text-gray-600">Use Yelp Fusion to refresh restaurant data into MySQL. Review snippets are limited by Yelp's public API.</p>
          <form onSubmit={syncYelp} className="mt-5 space-y-4">
            <input value={syncForm.location} onChange={(e) => setSyncForm((current) => ({ ...current, location: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" placeholder="Location" />
            <div className="grid gap-4 md:grid-cols-2">
              <input value={syncForm.term} onChange={(e) => setSyncForm((current) => ({ ...current, term: e.target.value }))} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" placeholder="Term" />
              <input type="number" min="1" max="50" value={syncForm.limit} onChange={(e) => setSyncForm((current) => ({ ...current, limit: e.target.value }))} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" placeholder="Limit" />
            </div>
            <button type="submit" disabled={syncState.loading} className="rounded-full bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
              {syncState.loading ? 'Syncing…' : 'Sync Yelp data'}
            </button>
            {syncState.message && <p className="text-sm text-green-700">{syncState.message}</p>}
            {syncState.error && <p className="text-sm text-red-700">{syncState.error}</p>}
          </form>
        </section>

        <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-950">Recent reviews</h2>
            <span className="text-sm text-gray-500">Across all owned restaurants</span>
          </div>
          <div className="space-y-4">
            {(dashboard?.recent_reviews || []).length === 0 ? (
              <p className="text-sm text-gray-500">No reviews yet.</p>
            ) : dashboard.recent_reviews.map((review) => (
              <div key={review.id} className="rounded-2xl bg-gray-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-gray-900">{review.author_name || review.user?.name || 'Anonymous'}</p>
                  <span className="text-sm text-red-600">{review.rating} / 5</span>
                </div>
                <p className="mt-2 text-sm text-gray-600">{review.body || 'No written review.'}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="mt-8">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-950">My restaurants</h2>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">Claim a listing from the restaurant page to manage it here.</span>
            <a href="/owner/new" className="rounded-full bg-brand-50 px-4 py-2 text-sm text-gray-700 border">Create new</a>
          </div>
        </div>
        <div className="space-y-5">
          {(dashboard?.restaurants || []).length === 0 ? (
            <div className="rounded-3xl border border-dashed border-gray-300 p-10 text-center text-gray-500">You have not claimed any restaurants yet.</div>
          ) : dashboard.restaurants.map((restaurant, index) => (
            <div key={restaurant.id}>
              <RestaurantCard restaurant={restaurant} index={index} horizontal actionLabel="Open analytics" onAction={() => { window.location.href = `/owner/restaurants/${restaurant.id}` }} />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
