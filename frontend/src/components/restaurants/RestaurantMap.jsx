import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'

// Inline SVG marker (same visual pin used elsewhere). Use explicit icon so this component
// does not depend on MapPreview having been imported first.
const pinSvg = `
  <svg xmlns='http://www.w3.org/2000/svg' width='30' height='42' viewBox='0 0 30 42'>
    <path fill='#ef4444' d='M15 0c6.627 0 12 5.373 12 12 0 9-12 30-12 30S3 21 3 12C3 5.373 8.373 0 15 0z' />
    <circle cx='15' cy='12' r='4' fill='#ffffff' />
  </svg>
`
const pinUrl = `data:image/svg+xml;utf8,${encodeURIComponent(pinSvg)}`

const restaurantIcon = L.icon({
  iconUrl: pinUrl,
  iconRetinaUrl: pinUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

export default function RestaurantMap({ latitude, longitude, name }) {
  if (!latitude || !longitude) return null

  const center = [Number(latitude), Number(longitude)]

  return (
    <div className="mb-4 overflow-hidden rounded-xl border border-gray-200">
      <div className="h-40 w-full">
        <MapContainer center={center} zoom={15} style={{ height: '100%', width: '100%' }} scrollWheelZoom={false} attributionControl={false} zoomControl={false}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={center} icon={restaurantIcon}>
            <Popup>
              <div className="text-sm">
                <div className="font-semibold">{name}</div>
              </div>
            </Popup>
          </Marker>
        </MapContainer>
      </div>
    </div>
  )
}
