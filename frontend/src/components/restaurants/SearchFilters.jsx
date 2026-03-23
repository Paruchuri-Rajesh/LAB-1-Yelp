import { CUISINES, PRICE_RANGES, SORT_OPTIONS } from '../../utils/constants'

const FILTER_CHIPS = [
  { label: 'Open Now', key: 'open_now' },
  { label: 'Reservations', key: 'has_reservations' },
  { label: 'Offers Delivery', key: 'offers_delivery' },
  { label: 'Offers Takeout', key: 'offers_takeout' },
]

export default function SearchFilters({ filters, onChange }) {
  const setValue = (key, value) => onChange({ ...filters, [key]: value })

  const toggle = (key) => onChange({ ...filters, [key]: !Boolean(filters[key]) })

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {FILTER_CHIPS.map((chip) => {
          const active = Boolean(filters?.[chip.key])
          return (
            <button
              key={chip.key}
              type="button"
              onClick={() => toggle(chip.key)}
              className={`rounded-full border px-4 py-2 text-sm hover:bg-gray-50 ${active ? 'bg-red-50 border-red-200 text-red-700' : 'border-gray-300 text-gray-700'}`}
            >
              {chip.label}
            </button>
          )
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-gray-700">Sort</span>
          <select value={filters.sort_by} onChange={(e) => setValue('sort_by', e.target.value)} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500">
            {SORT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>


        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-gray-700">Cuisine</span>
          <select value={filters.cuisine || ''} onChange={(e) => setValue('cuisine', e.target.value)} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500">
            <option value="">All cuisines</option>
            {CUISINES.map((cuisine) => <option key={cuisine} value={cuisine}>{cuisine}</option>)}
          </select>
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-gray-700">Price</span>
          <select value={filters.price_range || ''} onChange={(e) => setValue('price_range', e.target.value)} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500">
            <option value="">Any</option>
            {PRICE_RANGES.map((price) => <option key={price.value} value={price.value}>{price.label}</option>)}
          </select>
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-gray-700">Minimum rating</span>
          <select value={filters.min_rating || ''} onChange={(e) => setValue('min_rating', e.target.value)} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-red-500">
            <option value="">Any</option>
            <option value="4">4.0+</option>
            <option value="3">3.0+</option>
            <option value="2">2.0+</option>
          </select>
        </label>
      </div>
    </div>
  )
}
