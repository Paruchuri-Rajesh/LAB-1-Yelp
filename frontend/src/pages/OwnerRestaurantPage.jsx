import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getOwnerRestaurantDashboard, updateOwnedRestaurant } from '../api/owner'
import { uploadOwnedRestaurantPhotos, deleteOwnedRestaurantPhoto, updateOwnedRestaurantHours } from '../api/owner'
import Spinner from '../components/ui/Spinner'

function BreakdownBar({ label, value, total }) {
  const percent = total ? (value / total) * 100 : 0
  return (
    <div className="grid grid-cols-[40px_1fr_40px] items-center gap-3 text-sm text-gray-600">
      <span>{label}</span>
      <div className="h-3 overflow-hidden rounded-full bg-gray-100">
        <div className="h-full rounded-full bg-red-500" style={{ width: `${percent}%` }} />
      </div>
      <span>{value}</span>
    </div>
  )
}

export default function OwnerRestaurantPage() {
  const { id } = useParams()
  const [dashboard, setDashboard] = useState(null)
  const [form, setForm] = useState({ description: '', phone: '', website: '', price_range: '', image_url: '', address: '', city: '', state: '', zip_code: '' })
  const [photoFiles, setPhotoFiles] = useState([])
  const [photoUploading, setPhotoUploading] = useState(false)
  const [hoursForm, setHoursForm] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const response = await getOwnerRestaurantDashboard(id)
      setDashboard(response.data)
      setForm({
        description: response.data.restaurant.description || '',
        phone: response.data.restaurant.phone || '',
        website: response.data.restaurant.website || '',
        price_range: response.data.restaurant.price_range || '',
        image_url: response.data.restaurant.image_url || response.data.restaurant.primary_photo || '',
        address: response.data.restaurant.address || '',
        city: response.data.restaurant.city || '',
        state: response.data.restaurant.state || '',
        zip_code: response.data.restaurant.zip_code || '',
      })
      setHoursForm(response.data.restaurant.hours || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [id])

  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    setMessage('')
    try {
      await updateOwnedRestaurant(id, form)
      setMessage('Restaurant updated successfully.')
      await loadDashboard()
    } finally {
      setSaving(false)
    }
  }
  
  const onPhotoFiles = (e) => setPhotoFiles(Array.from(e.target.files || []))

  const uploadPhotos = async () => {
    if (!photoFiles.length) return
    setPhotoUploading(true)
    try {
      const fd = new FormData()
      photoFiles.forEach((f) => fd.append('photos', f))
      await uploadOwnedRestaurantPhotos(id, fd)
      setPhotoFiles([])
      await loadDashboard()
    } catch (err) {
      // TODO: show error
    } finally {
      setPhotoUploading(false)
    }
  }

  const removePhoto = async (photoId) => {
    try {
      await deleteOwnedRestaurantPhoto(id, photoId)
      await loadDashboard()
    } catch (err) {
      // TODO: show error
    }
  }

  const saveHours = async () => {
    try {
      await updateOwnedRestaurantHours(id, hoursForm)
      await loadDashboard()
    } catch (err) {
      // TODO: show error
    }
  }

  if (loading) return <div className="flex justify-center py-24"><Spinner className="h-10 w-10" /></div>
  if (!dashboard) return <div className="mx-auto max-w-3xl px-4 py-20 text-center text-gray-500">Restaurant analytics unavailable.</div>

  const totalRatings = Object.values(dashboard.rating_breakdown || {}).reduce((sum, value) => sum + value, 0)
  const DAYS = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8 flex items-center justify-between gap-4">
        <div>
          <Link to="/owner" className="text-sm font-semibold text-red-600">← Back to owner dashboard</Link>
          <h1 className="mt-3 text-4xl font-black tracking-tight text-gray-950">{dashboard.restaurant.name}</h1>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
        <section className="space-y-6">
          <div className="grid gap-5 md:grid-cols-3">
            <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-500">Views</p>
              <p className="mt-3 text-4xl font-black text-gray-950">{dashboard.total_views}</p>
            </div>
            <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-500">Reviews</p>
              <p className="mt-3 text-4xl font-black text-gray-950">{dashboard.total_reviews}</p>
            </div>
            <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-500">Average rating</p>
              <p className="mt-3 text-4xl font-black text-gray-950">{dashboard.avg_rating}</p>
            </div>
          </div>

          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-950">Ratings breakdown</h2>
            <div className="mt-5 space-y-3">
              {Object.entries(dashboard.rating_breakdown || {}).map(([label, value]) => (
                <BreakdownBar key={label} label={`${label}★`} value={value} total={totalRatings} />
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-950">Recent reviews</h2>
            <div className="mt-5 space-y-4">
              {(dashboard.recent_reviews || []).map((review) => (
                <div key={review.id} className="rounded-2xl bg-gray-50 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold text-gray-900">{review.author_name || review.user?.name || 'Anonymous'}</p>
                    <span className="text-sm text-red-600">{review.rating} / 5</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600">{review.body || 'No written review.'}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-bold text-gray-950">Edit restaurant details</h2>
          <div className="mt-4">
            <h3 className="text-lg font-semibold">Photos</h3>
            <div className="mt-3 grid grid-cols-3 gap-3">
              {(dashboard.restaurant.photos || []).map((p) => (
                <div key={p.id} className="relative overflow-hidden rounded-md">
                  <img src={p.file_path.startsWith('http') ? p.file_path : `/uploads/${p.file_path}`} className="h-40 w-full object-cover" />
                  <button onClick={() => removePhoto(p.id)} className="absolute right-2 top-2 rounded-full bg-white/80 px-2 py-1 text-xs text-red-600">Delete</button>
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-3">
              <input type="file" accept="image/*" multiple onChange={onPhotoFiles} />
              <button onClick={uploadPhotos} disabled={photoUploading} className="rounded-full bg-red-600 px-4 py-2 text-sm text-white">{photoUploading ? 'Uploading…' : 'Upload photos'}</button>
            </div>
          </div>

          <div className="mt-6">
            <h3 className="text-lg font-semibold">Hours</h3>
            <div className="mt-3 space-y-2">
              {(hoursForm || []).map((h, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <select value={h.day_of_week} onChange={(e) => setHoursForm((cur) => cur.map((it, i) => i === idx ? { ...it, day_of_week: e.target.value } : it))} className="w-32 rounded border px-2 py-1 text-sm">
                    {DAYS.map((d) => (
                      <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                    ))}
                  </select>
                  <input type="time" value={h.open_time || ''} onChange={(e) => setHoursForm((cur) => cur.map((it, i) => i === idx ? { ...it, open_time: e.target.value } : it))} className="rounded border px-2 py-1 text-sm" disabled={h.is_closed} />
                  <input type="time" value={h.close_time || ''} onChange={(e) => setHoursForm((cur) => cur.map((it, i) => i === idx ? { ...it, close_time: e.target.value } : it))} className="rounded border px-2 py-1 text-sm" disabled={h.is_closed} />
                  <label className="ml-2 flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={!!h.is_closed} onChange={(e) => setHoursForm((cur) => cur.map((it, i) => {
                      if (i !== idx) return it
                      const isClosed = e.target.checked
                      return { ...it, is_closed: isClosed, open_time: isClosed ? '' : (it.open_time || ''), close_time: isClosed ? '' : (it.close_time || '') }
                    }))} /> Closed</label>
                </div>
              ))}
              <div className="mt-2 flex gap-2">
                <button type="button" onClick={() => setHoursForm((cur) => [...cur, { day_of_week: 'monday', open_time: '', close_time: '', is_closed: false }])} className="rounded-full border px-3 py-1 text-sm">Add row</button>
                <button type="button" onClick={saveHours} className="rounded-full bg-red-600 px-3 py-1 text-sm text-white">Save hours</button>
              </div>
            </div>
          </div>
          <form onSubmit={save} className="mt-5 space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Address</span>
              <input value={form.address} onChange={(e) => setForm((current) => ({ ...current, address: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>

            <div className="grid grid-cols-3 gap-2">
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-gray-700">City</span>
                <input value={form.city} onChange={(e) => setForm((current) => ({ ...current, city: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-gray-700">State</span>
                <input value={form.state} onChange={(e) => setForm((current) => ({ ...current, state: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-gray-700">ZIP</span>
                <input value={form.zip_code} onChange={(e) => setForm((current) => ({ ...current, zip_code: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
              </label>
            </div>

            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Description</span>
              <textarea value={form.description} onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))} rows="5" className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Phone</span>
              <input value={form.phone} onChange={(e) => setForm((current) => ({ ...current, phone: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Website</span>
              <input value={form.website} onChange={(e) => setForm((current) => ({ ...current, website: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Price range</span>
              <input value={form.price_range} onChange={(e) => setForm((current) => ({ ...current, price_range: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" placeholder="$$" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-gray-700">Primary image URL</span>
              <input value={form.image_url} onChange={(e) => setForm((current) => ({ ...current, image_url: e.target.value }))} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </label>
            <button type="submit" disabled={saving} className="rounded-full bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
              {saving ? 'Saving…' : 'Save changes'}
            </button>
            {message && <p className="text-sm text-green-700">{message}</p>}
          </form>
        </section>
      </div>
    </div>
  )
}
