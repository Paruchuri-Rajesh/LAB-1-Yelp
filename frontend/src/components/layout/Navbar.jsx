import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import Avatar from '../ui/Avatar'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [menuOpen, setMenuOpen] = useState(false)
  const [search, setSearch] = useState({
    q: searchParams.get('q') || '',
    location: searchParams.get('location') || 'Union City, CA',
  })

  useEffect(() => {
    setSearch({
      q: searchParams.get('q') || '',
      location: searchParams.get('location') || 'Union City, CA',
    })
  }, [searchParams])

  const welcomeLabel = useMemo(() => (user?.is_owner ? 'Owner tools' : 'Restaurants'), [user])

  const submit = (event) => {
    event.preventDefault()
    const params = new URLSearchParams()
    if (search.q.trim()) params.set('q', search.q.trim())
    if (search.location.trim()) params.set('location', search.location.trim())
    navigate(`/search?${params.toString()}`)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-4">
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <span className="rounded-xl bg-red-600 px-3 py-2 text-xl font-black tracking-tight text-white">yelp</span>
        </Link>

        <form onSubmit={submit} className="hidden flex-1 items-center overflow-hidden rounded-2xl border border-gray-200 md:flex">
          <div className="flex flex-1 items-center gap-2 px-4">
            <input
              value={search.q}
              onChange={(e) => setSearch((current) => ({ ...current, q: e.target.value }))}
              placeholder="Restaurants"
              className="w-full py-3 text-sm outline-none"
            />
          </div>
          <div className="h-8 w-px bg-gray-200" />
          <div className="flex flex-1 items-center gap-2 px-4">
            <input
              value={search.location}
              onChange={(e) => setSearch((current) => ({ ...current, location: e.target.value }))}
              placeholder="Location"
              className="w-full py-3 text-sm outline-none"
            />
          </div>
          <button type="submit" className="m-1 rounded-2xl bg-red-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-red-700">
            Search
          </button>
        </form>

        <nav className="ml-auto flex items-center gap-4 text-sm">
          <Link to="/search" className="hidden text-gray-700 hover:text-red-600 md:block">{welcomeLabel}</Link>
          <Link to="/suggest" className="hidden text-gray-700 hover:text-red-600 md:block">Suggest</Link>
          {user?.is_owner && <Link to="/owner" className="hidden text-gray-700 hover:text-red-600 md:block">Owner Dashboard</Link>}
          {user ? (
            <div className="relative">
              <button onClick={() => setMenuOpen((open) => !open)} className="flex items-center gap-2 rounded-full border border-gray-200 px-2 py-1 hover:bg-gray-50">
                <Avatar user={user} size="sm" />
                <span className="hidden md:block">{user.name}</span>
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg">
                  <Link to="/profile" onClick={() => setMenuOpen(false)} className="block px-4 py-3 hover:bg-gray-50">Profile</Link>
                  <Link to="/profile/preferences" onClick={() => setMenuOpen(false)} className="block px-4 py-3 hover:bg-gray-50">Preferences</Link>
                  {user.is_owner && <Link to="/owner" onClick={() => setMenuOpen(false)} className="block px-4 py-3 hover:bg-gray-50">Owner Dashboard</Link>}
                  <button onClick={handleLogout} className="block w-full px-4 py-3 text-left text-red-600 hover:bg-red-50">Log out</button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link to="/login" className="font-medium text-gray-700 hover:text-red-600">Log In</Link>
              <Link to="/signup" className="rounded-full bg-red-600 px-4 py-2 font-semibold text-white hover:bg-red-700">Sign Up</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
