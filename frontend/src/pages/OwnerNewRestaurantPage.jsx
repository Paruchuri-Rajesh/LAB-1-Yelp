import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createOwnedRestaurant } from '../api/owner'
import Spinner from '../components/ui/Spinner'

export default function OwnerNewRestaurantPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', address: '', city: '', state: '', zip_code: '', phone: '', website: '', cuisine_type: '', price_range: '', description: '' })
  const [files, setFiles] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const onChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  const onFiles = (e) => setFiles(Array.from(e.target.files || []))

  const submit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => { if (v != null) fd.append(k, v) })
      files.forEach((f) => fd.append('photos', f))
      const { data } = await createOwnedRestaurant(fd)
      // on success, navigate to owner restaurant page
      navigate(`/owner/restaurants/${data.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create restaurant')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold mb-4">Create a new restaurant</h1>
      <form onSubmit={submit} className="space-y-4 bg-white border border-gray-200 rounded-xl p-6">
        <label className="block">
          <span className="text-sm text-gray-600">Name</span>
          <input name="name" value={form.name} onChange={onChange} required className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>

        <label className="block">
          <span className="text-sm text-gray-600">Address</span>
          <input name="address" value={form.address} onChange={onChange} className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>

        <div className="grid grid-cols-2 gap-2">
          <input name="city" value={form.city} onChange={onChange} placeholder="City" className="rounded-lg border px-3 py-2" />
          <input name="state" value={form.state} onChange={onChange} placeholder="State" className="rounded-lg border px-3 py-2" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <input name="zip_code" value={form.zip_code} onChange={onChange} placeholder="ZIP" className="rounded-lg border px-3 py-2" />
          <input name="phone" value={form.phone} onChange={onChange} placeholder="Phone" className="rounded-lg border px-3 py-2" />
        </div>

        <label className="block">
          <span className="text-sm text-gray-600">Website</span>
          <input name="website" value={form.website} onChange={onChange} className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>

        <label className="block">
          <span className="text-sm text-gray-600">Cuisine (comma separated)</span>
          <input name="cuisine_type" value={form.cuisine_type} onChange={onChange} className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>

        <label className="block">
          <span className="text-sm text-gray-600">Description</span>
          <textarea name="description" value={form.description} onChange={onChange} rows={4} className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>

        <label className="block">
          <span className="text-sm text-gray-600">Photos</span>
          <input type="file" accept="image/*" multiple onChange={onFiles} className="mt-2" />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end">
          <button type="submit" disabled={submitting} className="rounded-full bg-red-600 px-5 py-2 text-sm text-white">
            {submitting ? <Spinner className="h-5 w-5" /> : 'Create restaurant'}
          </button>
        </div>
      </form>
    </div>
  )
}
