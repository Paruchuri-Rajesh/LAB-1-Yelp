export function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

export function formatRating(rating) {
  if (rating == null) return '—'
  return Number(rating).toFixed(1)
}

export function formatPriceRange(price) {
  if (!price) return ''
  return price
}

export function getAvatarUrl(path) {
  if (!path) return null
  // If path is an absolute URL, return it directly; otherwise assume it's a server upload path
  if (typeof path === 'string' && (path.startsWith('http://') || path.startsWith('https://') || path.includes('://'))) {
    return path
  }
  return `/uploads/${path}`
}

export function getInitials(name = '') {
  return name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export function getMediaUrl(path) {
  if (!path) return null
  if (typeof path === 'string' && (path.startsWith('http://') || path.startsWith('https://') || path.includes('://'))) {
    return path
  }
  return `/uploads/${path}`
}
