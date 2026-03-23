import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { formatRating, getMediaUrl } from '../../utils/formatters'
import StarRating from '../ui/StarRating'
import { addFavorite, removeFavorite } from '../../api/users'

function ActionButton({ restaurant, actionLabel, onAction }) {
  if (onAction) {
    return (
      <button
        type="button"
        onClick={onAction}
        className="shrink-0 rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
      >
        {actionLabel}
      </button>
    )
  }

  return (
    <Link
      to={`/restaurants/${restaurant.id}`}
      className="shrink-0 rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
    >
      {actionLabel}
    </Link>
  )
}

export default function RestaurantCard({
  restaurant,
  index = 0,
  horizontal = false,
  actionLabel = 'View details',
  onAction,
  isFavorited = false,
}) {
  const [fav, setFav] = useState(!!isFavorited)
  const [favLoading, setFavLoading] = useState(false)

  const toggleFav = async () => {
    if (favLoading) return
    // optimistic UI
    const newFav = !fav
    setFav(newFav)
    setFavLoading(true)
    try {
      if (!newFav) {
        // user just unfavorited
        await removeFavorite(restaurant.id)
      } else {
        await addFavorite(restaurant.id)
      }
      // notify other parts of the app that favorites changed
      try {
        const ev = new CustomEvent('favorite:changed', { detail: { restaurantId: restaurant.id, favorited: newFav } })
        window.dispatchEvent(ev)
      } catch (e) {
        // ignore
      }
    } catch (err) {
      // revert on error
      setFav(!newFav)
      console.error('Favorite toggle failed', err)
    } finally {
      setFavLoading(false)
    }
  }

  // keep local state in sync if parent changes isFavorited prop
  useEffect(() => {
    setFav(!!isFavorited)
  }, [isFavorited])
  const image =
    getMediaUrl(restaurant.primary_photo || restaurant.image_url) ||
    'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80'

  const tags = String(restaurant.cuisine_type || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3)

  if (horizontal) {
    return (
      <div className="flex flex-col gap-4 rounded-3xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md md:flex-row">
        <Link
          to={`/restaurants/${restaurant.id}`}
          className="shrink-0 overflow-hidden rounded-2xl bg-gray-100 md:w-64"
        >
          <img src={image} alt={restaurant.name} className="h-48 w-full object-cover md:h-full" />
        </Link>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="mb-2 flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-red-50 text-sm font-bold text-red-600">
                  {index + 1}
                </span>
                  <h3 className="truncate text-2xl font-bold text-gray-900">{restaurant.name}</h3>
              </div>

              <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
                <StarRating value={restaurant.avg_rating} size={16} />
                <span className="font-semibold text-red-600">{formatRating(restaurant.avg_rating)}</span>
                <span>({restaurant.review_count} reviews)</span>
                {restaurant.price_range && <span>{restaurant.price_range}</span>}
                {restaurant.cuisine_type && <span>{restaurant.cuisine_type}</span>}
              </div>
            </div>

            <div className="hidden md:flex items-center gap-2">
              <button
                type="button"
                onClick={toggleFav}
                aria-pressed={fav}
                disabled={favLoading}
                className={`${fav ? 'text-red-600' : 'text-gray-400'} hover:text-red-600 ${favLoading ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                {fav ? '♥' : '♡'}
              </button>
              <div className="hidden md:block">
                <ActionButton restaurant={restaurant} actionLabel={actionLabel} onAction={onAction} />
              </div>
            </div>
          </div>

          <div className="mt-3 space-y-2 text-sm text-gray-600">
            <p className="break-words leading-6">
              {[restaurant.address, restaurant.city, restaurant.state].filter(Boolean).join(', ') || 'Address coming soon'}
            </p>
            <div className="flex flex-wrap gap-2">
              {tags.map((item) => (
                <span key={item} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">
                  {item}
                </span>
              ))}
              <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">
                {restaurant.source === 'yelp' ? 'Imported from Yelp' : 'Local listing'}
              </span>
            </div>
          </div>

          <div className="mt-4 md:hidden">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={toggleFav}
                aria-pressed={fav}
                disabled={favLoading}
                className={`${fav ? 'text-red-600' : 'text-gray-400'} hover:text-red-600 ${favLoading ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                {fav ? '♥' : '♡'}
              </button>
              <ActionButton restaurant={restaurant} actionLabel={actionLabel} onAction={onAction} />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-full overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm transition hover:shadow-md">
      <Link to={`/restaurants/${restaurant.id}`} className="block overflow-hidden bg-gray-100">
        <img src={image} alt={restaurant.name} className="h-56 w-full object-cover" />
      </Link>

      <div className="flex flex-col gap-3 p-4">
        <div className="min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="truncate text-xl font-extrabold text-slate-900">{restaurant.name}</h3>

              <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-600">
                <StarRating value={restaurant.avg_rating} size={16} />
                <span className="font-semibold text-red-500">{formatRating(restaurant.avg_rating)}</span>
                <span>({restaurant.review_count || 0} reviews)</span>
                {restaurant.price_range ? <span>{restaurant.price_range}</span> : null}
              </div>
            </div>

            <ActionButton restaurant={restaurant} actionLabel={actionLabel} onAction={onAction} />
          </div>

          <p className="mt-3 break-words text-base text-slate-700">{restaurant.cuisine_type}</p>

          <p className="mt-2 break-words text-sm leading-6 text-slate-500">
            {[restaurant.address, restaurant.city, restaurant.state].filter(Boolean).join(', ')}
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {tags.map((item) => (
              <span key={item} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">
                {item}
              </span>
            ))}
            {restaurant.source ? (
              <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                {restaurant.source === 'yelp' ? 'Imported from Yelp' : 'Local listing'}
              </span>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}
