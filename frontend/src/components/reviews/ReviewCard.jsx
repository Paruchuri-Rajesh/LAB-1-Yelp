import { useState } from 'react'
import Avatar from '../ui/Avatar'
import { Link } from 'react-router-dom'
import StarRating from '../ui/StarRating'
import { formatDate, getMediaUrl } from '../../utils/formatters'
import { useAuth } from '../../contexts/AuthContext'
import { updateReview, deleteReview } from '../../api/restaurants'

export default function ReviewCard({ review, restaurantId, onUpdated, onDeleted }) {
  const { user } = useAuth()
  const isOwn = user?.id === review.user_id && review.source === 'local'

  const [editing, setEditing] = useState(false)
  const [editRating, setEditRating] = useState(review.rating)
  const [editBody, setEditBody] = useState(review.body || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      const { data } = await updateReview(restaurantId, review.id, { rating: editRating, body: editBody })
      onUpdated?.(data)
      setEditing(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save.')
    } finally {
      setSaving(false)
    }
  }

  const remove = async () => {
    if (!window.confirm('Delete your review?')) return
    await deleteReview(restaurantId, review.id)
    onDeleted?.(review.id)
  }

  const displayUser = review.user || { name: review.author_name || 'Anonymous', profile_picture_path: null }

  return (
    <div className="border-b border-gray-100 py-5 last:border-0">
      <div className="flex items-start gap-3">
        <Avatar user={displayUser} size="md" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-gray-900 text-sm">{review.user?.name || review.author_name || 'Anonymous'}</span>
            {review.restaurant_name ? (
              <Link to={`/restaurants/${restaurantId || review.restaurant_id}`} className="text-sm text-gray-500 hover:text-red-600">· {review.restaurant_name}</Link>
            ) : null}
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-gray-500">{review.source}</span>
            <span className="text-xs text-gray-400">{formatDate(review.created_at || review.visited_at)}</span>
          </div>

          {editing ? (
            <div className="mt-2 space-y-2">
              <StarRating value={editRating} onChange={setEditRating} size="md" />
              <textarea
                value={editBody}
                onChange={(e) => setEditBody(e.target.value)}
                rows={3}
                className="w-full rounded-2xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
              />
              {error && <p className="text-xs text-red-600">{error}</p>}
              <div className="flex gap-2">
                <button onClick={save} disabled={saving} className="rounded-full bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-60">
                  {saving ? 'Saving…' : 'Save'}
                </button>
                <button onClick={() => setEditing(false)} className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
              </div>
            </div>
          ) : (
            <>
              <div className="mt-2"><StarRating value={review.rating} readonly size="sm" /></div>
              {review.title && <p className="mt-2 text-sm font-medium text-gray-800">{review.title}</p>}
              {review.body && <p className="mt-2 text-sm leading-relaxed text-gray-600">{review.body}</p>}
              {review.photos && review.photos.length > 0 && (
                <div className="mt-3 grid grid-cols-3 gap-2">
                  {review.photos.map((p) => {
                    const src = getMediaUrl(p.file_path || p)
                    return (
                      <img key={p.id || src} src={src} alt={p.caption || 'review photo'} className="w-full h-28 object-cover rounded-md" />
                    )
                  })}
                </div>
              )}
            </>
          )}
        </div>

        {isOwn && !editing && (
          <div className="flex gap-1 shrink-0">
            <button onClick={() => setEditing(true)} className="rounded-full px-3 py-1 text-xs text-gray-500 hover:bg-gray-50 hover:text-red-600">Edit</button>
            <button onClick={remove} className="rounded-full px-3 py-1 text-xs text-gray-500 hover:bg-red-50 hover:text-red-600">Delete</button>
          </div>
        )}
      </div>
    </div>
  )
}
