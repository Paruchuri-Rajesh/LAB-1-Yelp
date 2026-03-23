import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getRestaurant, getReviews } from '../api/restaurants'
import { claimRestaurant } from '../api/owner'
import { useAuth } from '../contexts/AuthContext'
import Spinner from '../components/ui/Spinner'
import ReviewCard from '../components/reviews/ReviewCard'
import ReviewForm from '../components/reviews/ReviewForm'
import { formatRating, getMediaUrl } from '../utils/formatters'
import RestaurantMap from '../components/restaurants/RestaurantMap'
import StarRating from '../components/ui/StarRating'

const DAY_ORDER = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

function formatHour(value) {
  if (!value) return '—'
  const [hour, minute] = value.split(':').map(Number)
  const suffix = hour >= 12 ? 'PM' : 'AM'
  const normalized = hour % 12 || 12
  return `${normalized}:${String(minute).padStart(2, '0')} ${suffix}`
}

export default function RestaurantPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const [restaurant, setRestaurant] = useState(null)
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [reviewsLoading, setReviewsLoading] = useState(true)
  const [claimState, setClaimState] = useState({ loading: false, message: '', error: '' })

  useEffect(() => {
    setLoading(true)
    getRestaurant(id)
      .then((response) => setRestaurant(response.data))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    setReviewsLoading(true)
    getReviews(id)
      .then((response) => setReviews(response.data.items))
      .finally(() => setReviewsLoading(false))
  }, [id])

  const hasReviewed = useMemo(() => reviews.some((review) => review.user_id === user?.id), [reviews, user])
  const heroImage = getMediaUrl(restaurant?.photos?.[0]?.file_path || restaurant?.image_url) || 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1400&q=80'

  // Build a combined gallery: restaurant photos + photos attached to reviews
  const galleryPhotos = useMemo(() => {
    const pics = []
    if (restaurant?.photos && restaurant.photos.length > 0) {
      restaurant.photos.forEach((p) => pics.push({ id: `r-${p.id}`, file_path: p.file_path, caption: p.caption }))
    }
    if (reviews && reviews.length > 0) {
      reviews.forEach((rev) => {
        if (rev.photos && rev.photos.length > 0) {
          rev.photos.forEach((p) => pics.push({ id: `rev-${p.id}`, file_path: p.file_path, caption: p.caption }))
        }
      })
    }
    // dedupe by file_path
    const seen = new Set()
    return pics.filter((p) => {
      if (!p?.file_path) return false
      if (seen.has(p.file_path)) return false
      seen.add(p.file_path)
      return true
    })
  }, [restaurant, reviews])

  const handleClaim = async () => {
    setClaimState({ loading: true, message: '', error: '' })
    try {
      await claimRestaurant(id)
      setClaimState({ loading: false, message: 'Restaurant claimed. Open Owner Dashboard to manage it.', error: '' })
    } catch (error) {
      setClaimState({ loading: false, message: '', error: error.response?.data?.detail || 'Could not claim restaurant.' })
    }
  }

  if (loading) return <div className="flex justify-center py-24"><Spinner className="h-10 w-10" /></div>
  if (!restaurant) return <div className="mx-auto max-w-3xl px-4 py-24 text-center text-gray-500">Restaurant not found.</div>

  return (
    <div className="pb-12">
      <section className="border-b border-gray-200 bg-black text-white">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
          <div className="space-y-4">
            <div className="overflow-hidden rounded-[2rem] border border-white/10">
              <img src={heroImage} alt={restaurant.name} className="h-[320px] w-full object-cover" />
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tight">{restaurant.name}</h1>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-white/80">
                <StarRating value={Math.round(restaurant.avg_rating)} readonly size="md" />
                <span className="ml-1 font-bold text-red-300">{formatRating(restaurant.avg_rating)}</span>
                <span>{restaurant.review_count} reviews</span>
                {restaurant.price_range && <span>{restaurant.price_range}</span>}
                {restaurant.cuisine_type && <span>{restaurant.cuisine_type}</span>}
              </div>
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-white/10 p-6 backdrop-blur">
            <div className="space-y-3 text-sm text-white/85">
              <RestaurantMap latitude={restaurant.latitude} longitude={restaurant.longitude} name={restaurant.name} />
              <p>{restaurant.address}</p>
              <p>{restaurant.city}{restaurant.state ? `, ${restaurant.state}` : ''}{restaurant.zip_code ? ` ${restaurant.zip_code}` : ''}</p>
              {restaurant.phone && <p>{restaurant.phone}</p>}
              {restaurant.website && (
                <a href={restaurant.website} target="_blank" rel="noreferrer" className="inline-flex text-red-200 underline-offset-4 hover:underline">
                  Visit website
                </a>
              )}
            </div>
            {user?.is_owner && (
              <div className="mt-6 space-y-3">
                <button type="button" onClick={handleClaim} disabled={claimState.loading} className="rounded-full bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
                  {claimState.loading ? 'Claiming…' : 'Claim this restaurant'}
                </button>
                {claimState.message && <p className="text-sm text-green-200">{claimState.message}</p>}
                {claimState.error && <p className="text-sm text-red-200">{claimState.error}</p>}
              </div>
            )}
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="space-y-8">
          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-950">About this place</h2>
            <p className="mt-3 text-gray-600">{restaurant.description || 'Imported from Yelp API and ready for owner customization.'}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              {(restaurant.amenities || []).slice(0, 8).map((item) => (
                <span key={item} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">{item}</span>
              ))}
            </div>
          </div>

          {/* Photos gallery (includes restaurant photos + review photos) */}
          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-950">Photos</h2>
            {galleryPhotos && galleryPhotos.length > 0 ? (
              <div className="mt-4 grid grid-cols-3 gap-3">
                {galleryPhotos.map((p) => (
                  <a key={p.id} href={getMediaUrl(p.file_path)} target="_blank" rel="noreferrer">
                    <img src={getMediaUrl(p.file_path)} alt={p.caption || restaurant.name} className="w-full h-48 object-cover rounded-md" />
                  </a>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-sm text-gray-500">No photos uploaded yet.</p>
            )}
          </div>

          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between gap-4">
              <h2 className="text-2xl font-bold text-gray-950">Reviews</h2>
              {!user && <Link to="/login" className="text-sm font-semibold text-red-600">Log in to write a review</Link>}
            </div>
            {user && !hasReviewed && !user.is_owner && (
              <ReviewForm restaurantId={id} onCreated={(review) => setReviews((current) => [review, ...current])} />
            )}
            {user && !hasReviewed && user.is_owner && (
              <p className="mb-5 text-sm text-gray-500">Owners are not allowed to post reviews.</p>
            )}
            {user && hasReviewed && <p className="mb-5 text-sm text-gray-500">You already reviewed this restaurant.</p>}

            {reviewsLoading ? (
              <div className="flex justify-center py-14"><Spinner /></div>
            ) : reviews.length === 0 ? (
              <p className="text-sm text-gray-500">No reviews yet.</p>
            ) : (
              <div>
                {reviews.map((review) => (
                  <ReviewCard
                    key={review.id}
                    review={review}
                    restaurantId={id}
                    onUpdated={(updated) => setReviews((current) => current.map((item) => item.id === updated.id ? updated : item))}
                    onDeleted={(reviewId) => setReviews((current) => current.filter((item) => item.id !== reviewId))}
                  />
                ))}
              </div>
            )}
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="text-xl font-bold text-gray-950">Hours</h3>
            <div className="mt-4 space-y-3 text-sm text-gray-600">
              {DAY_ORDER.map((day) => {
                const hour = (restaurant.hours || []).find((item) => item.day_of_week === day)
                return (
                  <div key={day} className="flex items-center justify-between rounded-2xl bg-gray-50 px-4 py-3">
                    <span className="font-medium capitalize">{day}</span>
                    <span>{hour ? `${formatHour(hour.open_time)} - ${formatHour(hour.close_time)}` : 'Unavailable'}</span>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="text-xl font-bold text-gray-950">Owner tools</h3>
            <p className="mt-3 text-sm text-gray-600">Owners can claim this restaurant, view analytics, and update restaurant details from the dashboard.</p>
            {user?.is_owner ? (
              <Link to="/owner" className="mt-4 inline-flex rounded-full bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700">
                Open owner dashboard
              </Link>
            ) : (
              <Link to="/signup" className="mt-4 inline-flex rounded-full border border-gray-300 px-5 py-3 text-sm font-semibold text-gray-900 hover:bg-gray-50">
                Create owner account
              </Link>
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
