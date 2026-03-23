import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import SearchBar from '../components/restaurants/SearchBar'
import SearchFilters from '../components/restaurants/SearchFilters'
import RestaurantCard from '../components/restaurants/RestaurantCard'
import MapPreview from '../components/restaurants/MapPreview'
import Spinner from '../components/ui/Spinner'
import { searchRestaurants } from '../api/restaurants'

const DEFAULT_FILTERS = {
  sort_by: 'recommended',
  cuisine: '',
  price_range: '',
  min_rating: '',
  // filter chips
  open_now: false,
  has_reservations: false,
  offers_delivery: false,
  offers_takeout: false,
}

export default function SearchPage() {
  const [searchParams] = useSearchParams()
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(false)
  const [userLocation, setUserLocation] = useState(null)

  const q = searchParams.get('q') || ''
  // Only include location if the user explicitly provided it via the query params.
  // Previously we defaulted to a city which caused searches to always be location-scoped
  // and hid newly suggested restaurants that didn't have that city populated.
  const location = searchParams.get('location') || null
  const latParam = searchParams.get('lat')
  const lonParam = searchParams.get('lon')
  const [filters, setFilters] = useState({
    ...DEFAULT_FILTERS,
    cuisine: searchParams.get('cuisine') || '',
  })

  useEffect(() => {
    setFilters((current) => ({
      ...current,
      cuisine: searchParams.get('cuisine') || '',
    }))
  }, [searchParams])

  const fetchResults = useCallback(async (pageNumber = 1, nextFilters = filters) => {
    setLoading(true)
    try {
      const params = {
        page: pageNumber,
        page_size: 8,
        sort_by: nextFilters.sort_by,
        location,
      }
      if (q) params.q = q
      if (nextFilters.cuisine) params.cuisine = nextFilters.cuisine
      if (nextFilters.price_range) params.price_range = nextFilters.price_range
      if (nextFilters.min_rating) params.min_rating = nextFilters.min_rating
      // add filter chip params when enabled
      if (nextFilters.open_now) params.open_now = true
      if (nextFilters.has_reservations) params.has_reservations = true
      if (nextFilters.offers_delivery) params.offers_delivery = true
      if (nextFilters.offers_takeout) params.offers_takeout = true
      const response = await searchRestaurants(params)
      setResults(response.data.items)
      setTotal(response.data.total)
      setPages(response.data.pages || 1)
      setPage(pageNumber)
    } catch {
      setResults([])
      setTotal(0)
      setPages(1)
    } finally {
      setLoading(false)
    }
  }, [filters, location, q])

  useEffect(() => {
    fetchResults(1, filters)
  }, [filters, fetchResults])

  useEffect(() => {
    if (latParam && lonParam) {
      const lat = Number(latParam)
      const lon = Number(lonParam)
      if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
        setUserLocation({ latitude: lat, longitude: lon })
      }
    } else {
      setUserLocation(null)
    }
  }, [latParam, lonParam])

  const subtitle = useMemo(() => {
    if (q) return location ? `Best restaurants matching “${q}” near ${location}` : `Best restaurants matching “${q}”`
    return location ? `Best restaurants near ${location}` : `Best restaurants`
  }, [location, q])

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 space-y-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">Restaurants</p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-gray-950">{subtitle}</h1>
        </div>
        <SearchBar initialQuery={q} initialCuisine={filters.cuisine} initialLocation={location} compact />
        <SearchFilters filters={filters} onChange={setFilters} />
      </div>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_36%]">
        <section>
          <div className="mb-5 flex items-center justify-between">
            <p className="text-sm text-gray-600">{loading ? 'Searching…' : `${total} results`}</p>
            <p className="text-sm text-gray-600">Sort: <span className="font-semibold text-gray-900">{filters.sort_by}</span></p>
          </div>

          {loading ? (
            <div className="flex justify-center py-24"><Spinner className="h-10 w-10" /></div>
          ) : results.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-gray-300 p-12 text-center text-gray-500">No restaurants found. Try a broader location or fewer filters.</div>
          ) : (
            <div className="space-y-5">
              {results.map((restaurant, index) => (
                <RestaurantCard key={restaurant.id} restaurant={restaurant} index={index + (page - 1) * 8} horizontal />
              ))}
            </div>
          )}

          {pages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-3">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => fetchResults(page - 1)}
                className="rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-700 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">Page {page} of {pages}</span>
              <button
                type="button"
                disabled={page >= pages}
                onClick={() => fetchResults(page + 1)}
                className="rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </section>

        <aside>
            <MapPreview restaurants={results} userLocation={userLocation} />
        </aside>
      </div>
    </div>
  )
}
