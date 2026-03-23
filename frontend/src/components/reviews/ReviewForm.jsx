import { useState, useEffect } from 'react'
import StarRating from '../ui/StarRating'
import { createReview, uploadReviewPhotos } from '../../api/restaurants'

export default function ReviewForm({ restaurantId, onCreated }) {
  const [rating, setRating] = useState(0)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [files, setFiles] = useState([])
  const [previews, setPreviews] = useState([])

  const submit = async (e) => {
    e.preventDefault()
    if (!rating) { setError('Please select a star rating.'); return }
    setSubmitting(true)
    setError('')
    try {
      const { data } = await createReview(restaurantId, { rating, title: title || null, body: body || null })
      // if user selected photos, upload them after creating the review
      if (files && files.length > 0) {
        const form = new FormData()
        files.forEach((f) => form.append('photos', f))
        try {
          await uploadReviewPhotos(restaurantId, data.id, form)
        } catch (err) {
          // non-fatal: still consider the review created but surface error
          console.error('Failed to upload review photos', err)
        }
      }
      onCreated?.(data)
      setRating(0)
      setTitle('')
      setBody('')
      setFiles([])
      setPreviews([])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit review.')
    } finally {
      setSubmitting(false)
    }
  }

  useEffect(() => {
    // revoke object URLs on unmount or when previews change
    return () => {
      previews.forEach((p) => URL.revokeObjectURL(p))
    }
  }, [previews])

  const onFilesChange = (e) => {
    const list = Array.from(e.target.files || [])
    setFiles(list)
    const urls = list.map((f) => URL.createObjectURL(f))
    setPreviews(urls)
  }

  return (
    <form onSubmit={submit} className="bg-gray-50 border border-gray-200 rounded-xl p-5 space-y-4">
      <h3 className="font-semibold text-gray-900">Write a Review</h3>

      <div>
        <label className="block text-sm text-gray-600 mb-1">Your Rating</label>
        <StarRating value={rating} onChange={setRating} size="lg" />
      </div>

      <label className="block">
        <span className="text-sm text-gray-600">Title (optional)</span>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Summarize your visit"
          className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </label>

      <label className="block">
        <span className="text-sm text-gray-600">Review</span>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={4}
          placeholder="Tell others about your experience..."
          className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </label>

      <label className="block">
        <span className="text-sm text-gray-600">Photos (optional)</span>
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={onFilesChange}
          className="mt-2"
        />

        {previews.length > 0 && (
          <div className="mt-2 grid grid-cols-4 gap-2">
            {previews.map((p, idx) => (
              <img key={p} src={p} alt={`preview-${idx}`} className="w-full h-20 object-cover rounded-md border" />
            ))}
          </div>
        )}
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-brand-600 text-white py-2.5 rounded-lg font-medium hover:bg-brand-700 disabled:opacity-60 transition"
      >
        {submitting ? 'Submitting…' : 'Submit Review'}
      </button>
    </form>
  )
}
