import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CUISINES } from '../../utils/constants'

export default function SearchBar({ initialQuery = '', initialCuisine = '', initialLocation = '', compact = false }) {
  const navigate = useNavigate()
  const [q, setQ] = useState(initialQuery)
  const [cuisine, setCuisine] = useState(initialCuisine)
  const [location, setLocation] = useState(initialLocation)
  const [loadingLocation, setLoadingLocation] = useState(false)

  useEffect(() => setQ(initialQuery), [initialQuery])
  useEffect(() => setCuisine(initialCuisine), [initialCuisine])
  useEffect(() => setLocation(initialLocation), [initialLocation])

  const submit = (event) => {
    event.preventDefault()
    const params = new URLSearchParams()
    if (q.trim()) params.set('q', q.trim())
    if (location.trim()) params.set('location', location.trim())
    if (cuisine) params.set('cuisine', cuisine)
    navigate(`/search?${params.toString()}`)
  }

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      // not supported
      return
    }
    setLoadingLocation(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords
        setLocation('Current location')
        const params = new URLSearchParams()
        if (q.trim()) params.set('q', q.trim())
        if (cuisine) params.set('cuisine', cuisine)
        // include lat/lon so page can render user marker (backend doesn't use these)
        params.set('lat', String(latitude))
        params.set('lon', String(longitude))
        navigate(`/search?${params.toString()}`)
        setLoadingLocation(false)
      },
      () => {
        setLoadingLocation(false)
      },
      { timeout: 10000 }
    )
  }

  return (
    <form onSubmit={submit} className={`w-full ${compact ? '' : 'rounded-3xl border border-gray-200 bg-white p-3 shadow-sm'}`}>
      <div className={`grid gap-3 ${compact ? 'md:grid-cols-[1.3fr_1fr_auto]' : 'md:grid-cols-[1.4fr_1fr_220px_auto]'}`}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="restaurants, delivery, tacos, coffee..."
          className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none ring-red-500 transition focus:ring-2"
        />
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Union City, CA 94587"
          className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none ring-red-500 transition focus:ring-2"
        />
        <button
          type="button"
          onClick={useMyLocation}
          disabled={loadingLocation}
          className="hidden items-center gap-2 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 transition hover:bg-gray-50 md:flex"
        >
          {loadingLocation ? 'Locating…' : 'Use my location'}
        </button>
        {!compact && (
          <select
            value={cuisine}
            onChange={(e) => setCuisine(e.target.value)}
            className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none ring-red-500 transition focus:ring-2"
          >
            <option value="">All cuisines</option>
            {CUISINES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        )}
        <button type="submit" className="rounded-2xl bg-red-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-red-700">
          Search
        </button>
      </div>
    </form>
  )
}
