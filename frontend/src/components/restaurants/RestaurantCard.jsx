import { Link } from 'react-router-dom'
import { formatRating, getMediaUrl } from '../../utils/formatters'
import StarRating from '../ui/StarRating'

export default function RestaurantCard({ restaurant, index = 0, horizontal = false, actionLabel = 'View details', onAction }) {
  const image = getMediaUrl(restaurant.primary_photo || restaurant.image_url) || 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80'

  if (horizontal) {
    return (
      <div className="flex flex-col gap-4 rounded-3xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md md:flex-row">
        <Link to={`/restaurants/${restaurant.id}`} className="md:w-64 shrink-0 overflow-hidden rounded-2xl bg-gray-100">
          <img src={image} alt={restaurant.name} className="h-48 w-full object-cover md:h-full" />
        </Link>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-red-50 text-sm font-bold text-red-600">{index + 1}</span>
                <h3 className="text-2xl font-bold text-gray-900">{restaurant.name}</h3>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
                <StarRating value={restaurant.avg_rating} size={16} />
                <span className="ml-1 font-semibold text-red-600">{formatRating(restaurant.avg_rating)}</span>
                <span>({restaurant.review_count} reviews)</span>
                {restaurant.price_range && <span>{restaurant.price_range}</span>}
                {restaurant.cuisine_type && <span>{restaurant.cuisine_type}</span>}
              </div>
            </div>
            {onAction ? (
              <button type="button" onClick={onAction} className="hidden self-center rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 md:block">
                {actionLabel}
              </button>
            ) : (
              <Link to={`/restaurants/${restaurant.id}`} className="hidden self-center rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 md:block">
                {actionLabel}
              </Link>
            )}
          </div>

          <div className="mt-3 space-y-2 text-sm text-gray-600">
            <p>{restaurant.address || 'Address coming soon'}{restaurant.city ? `, ${restaurant.city}` : ''}{restaurant.state ? `, ${restaurant.state}` : ''}</p>
            <div className="flex flex-wrap gap-2">
              {(restaurant.cuisine_type || '').split(',').filter(Boolean).slice(0, 3).map((item) => (
                <span key={item} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">{item.trim()}</span>
              ))}
              <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">{restaurant.source === 'yelp' ? 'Imported from Yelp' : 'Local listing'}</span>
            </div>
          </div>

          <div className="mt-4 md:hidden">
            {onAction ? (
              <button type="button" onClick={onAction} className="self-center rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700">
                {actionLabel}
              </button>
            ) : (
              <Link to={`/restaurants/${restaurant.id}`} className="self-center rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700">
                {actionLabel}
              </Link>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <Link to={`/restaurants/${restaurant.id}`} className="overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <img src={image} alt={restaurant.name} className="h-48 w-full object-cover" />
      <div className="space-y-2 p-5">
  <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-bold text-gray-900">{restaurant.name}</h3>
          {restaurant.price_range && <span className="text-sm text-gray-500">{restaurant.price_range}</span>}
        </div>
        <div className="text-sm text-gray-600">
          <StarRating value={restaurant.avg_rating} size={16} />
          <span className="ml-1 font-semibold text-red-600">{formatRating(restaurant.avg_rating)}</span>
          <span className="ml-2">({restaurant.review_count} reviews)</span>
        </div>
        <p className="text-sm text-gray-500">{restaurant.cuisine_type}</p>
      </div>
    </Link>
  )
}
