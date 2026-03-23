import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, useMap } from 'react-leaflet'
import L from 'leaflet'
import { Link } from 'react-router-dom'

// Use an inline SVG data URL for the marker icon to avoid asset resolution issues
const pinSvg = `
  <svg xmlns='http://www.w3.org/2000/svg' width='30' height='42' viewBox='0 0 30 42'>
    <path fill='#ef4444' d='M15 0c6.627 0 12 5.373 12 12 0 9-12 30-12 30S3 21 3 12C3 5.373 8.373 0 15 0z' />
    <circle cx='15' cy='12' r='4' fill='#ffffff' />
  </svg>
`
const pinUrl = `data:image/svg+xml;utf8,${encodeURIComponent(pinSvg)}`

L.Icon.Default.mergeOptions({
  iconUrl: pinUrl,
  iconRetinaUrl: pinUrl,
  shadowUrl: null,
  // Explicitly set sizes/anchors so bundlers and CSS resets don't change layout
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function ImperativeMarkerLayer({ points = [], userLocation = null }) {
  const map = useMap()

  useEffect(() => {
    if (!map) return
    const created = []

    points.forEach((p) => {
      try {
        const icon = L.icon({
          iconUrl: pinUrl,
          iconRetinaUrl: pinUrl,
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
        })

        const m = L.marker([p.latitude, p.longitude], { title: p.name, icon }).addTo(map)
        const popupHtml = `
          <div class="text-sm">
            <div class="font-semibold">${p.name}</div>
            <div class="text-xs text-gray-600">${p.avg_rating || '—'} • ${p.review_count || 0} reviews</div>
            <div class="mt-2"><a href="/restaurants/${p.id}" class="text-xs font-semibold text-red-600">View details</a></div>
          </div>
        `
        m.bindPopup(popupHtml)
        created.push(m)
      } catch (err) {
        // ignore individual marker errors
        // console.warn('marker add failed', err)
      }
    })

    // add user location marker as a blue circle marker (imperative)
    let userMarker = null
    if (userLocation && userLocation.latitude && userLocation.longitude) {
      try {
        userMarker = L.circleMarker([Number(userLocation.latitude), Number(userLocation.longitude)], {
          radius: 8,
          color: '#2563eb',
          fillColor: '#2563eb',
        }).addTo(map)
        userMarker.bindPopup('<div class="text-sm">Your location</div>')
      } catch (err) {
        // ignore
      }
    }

    return () => {
      created.forEach((m) => {
        try {
          map.removeLayer(m)
        } catch (e) {}
      })
      if (userMarker) {
        try {
          map.removeLayer(userMarker)
        } catch (e) {}
      }
    }
  }, [map, JSON.stringify(points), userLocation])

  return null
}

function FitBounds({ points = [], userLocation = null }) {
  const map = useMap()
  useEffect(() => {
    const latlngs = []
    points.forEach((p) => {
      if (p.latitude && p.longitude) latlngs.push([Number(p.latitude), Number(p.longitude)])
    })
    if (userLocation && userLocation.latitude && userLocation.longitude) {
      latlngs.push([Number(userLocation.latitude), Number(userLocation.longitude)])
    }
    if (latlngs.length === 0) return
    try {
      map.fitBounds(latlngs, { padding: [40, 40] })
    } catch (err) {
      // ignore
    }
  }, [points, userLocation, map])
  return null
}

export default function MapPreview({ restaurants = [], userLocation = null, onRedo = null }) {
  const points = restaurants.filter((r) => r.latitude && r.longitude).map((r) => ({
    id: r.id,
    name: r.name,
    latitude: Number(r.latitude),
    longitude: Number(r.longitude),
    avg_rating: r.avg_rating,
    review_count: r.review_count,
  }))

  const center = points.length ? [points[0].latitude, points[0].longitude] : [37.7749, -122.4194]

  const mapRef = useRef(null)

  const handleRedo = () => {
    if (!mapRef.current || typeof onRedo !== 'function') return
    try {
      const bounds = mapRef.current.getBounds()
      const ne = bounds.getNorthEast()
      const sw = bounds.getSouthWest()
      const center = mapRef.current.getCenter()
      onRedo({ ne: [ne.lat, ne.lng], sw: [sw.lat, sw.lng], center: [center.lat, center.lng] })
    } catch (err) {
      // ignore
    }
  }

  return (
    <div className="sticky top-28 overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div>
          <p className="text-sm font-semibold text-gray-900">Map preview</p>
          <p className="text-xs text-gray-500">Restaurant pins update with current results</p>
        </div>
        <button
          type="button"
          onClick={handleRedo}
          className="rounded-full bg-red-600 px-4 py-2 text-xs font-semibold text-white"
        >
          Redo search in map
        </button>
      </div>

      <div className="h-[540px]">
        <MapContainer whenCreated={(m) => (mapRef.current = m)} center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <FitBounds points={points} userLocation={userLocation} />
          <ImperativeMarkerLayer points={points} userLocation={userLocation} />
        </MapContainer>
      </div>
    </div>
  )
}
