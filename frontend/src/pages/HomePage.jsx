import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import SearchBar from '../components/restaurants/SearchBar'
import heroImage from '../assets/hero.png'
import RestaurantCard from '../components/restaurants/RestaurantCard'
import Spinner from '../components/ui/Spinner'
import { searchRestaurants } from '../api/restaurants'
import { useAuth } from '../contexts/AuthContext'
import ChatWidget from '../components/chat/ChatWidget'

const QUICK_LINKS = [
  'Dinner tonight',
  'Outdoor seating',
  'Best rated near me',
  'Brunch spots',
]

export default function HomePage() {
  const { user } = useAuth()
  const [featured, setFeatured] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // default to San Francisco which matches seeded data used during development
    searchRestaurants({ sort_by: 'recommended', page_size: 6, location: 'San Francisco, CA' })
      .then((response) => setFeatured(response.data.items))
      .catch(() => setFeatured([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <section className="border-b border-gray-200 bg-[linear-gradient(180deg,#fff_0%,#fff5f5_100%)] px-4 py-14">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <p className="mb-4 inline-flex rounded-full bg-red-50 px-4 py-2 text-sm font-semibold text-red-600">Yelp-style restaurant discovery</p>
            <h1 className="max-w-2xl text-5xl font-black tracking-tight text-gray-950 md:text-6xl">Find great restaurants, import fresh Yelp data, and manage owner dashboards.</h1>
            <p className="mt-5 max-w-2xl text-lg text-gray-600">
              Browse local places with a Yelp-inspired layout, sync restaurant data into MySQL, and give restaurant owners analytics for views and reviews.
            </p>
            <div className="mt-8 max-w-4xl">
              <SearchBar initialLocation="Union City, CA 94587" />
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              {QUICK_LINKS.map((item) => (
                <button key={item} type="button" className="rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-white">
                  {item}
                </button>
              ))}
            </div>
          </div>
          <div className="overflow-hidden rounded-[2rem] border border-gray-200 bg-white shadow-xl">
            <img src={heroImage} alt="Restaurant preview" className="h-full w-full object-cover" />
          </div>
        </div>
      </section>

        {/* Chat widget */}
        <ChatWidget />

      <section className="mx-auto max-w-7xl px-4 py-14">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-3xl font-black text-gray-950">Top restaurants</h2>
            <p className="mt-2 text-gray-600">These cards use live search results from your backend.</p>
          </div>
          <Link to="/search?location=Union%20City%2C%20CA" className="rounded-full border border-gray-300 px-5 py-3 text-sm font-semibold text-gray-900 hover:bg-gray-50">
            View all results
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-20"><Spinner className="h-10 w-10" /></div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {featured.map((restaurant) => <RestaurantCard key={restaurant.id} restaurant={restaurant} />)}
          </div>
        )}
      </section>

      <section className="border-t border-gray-200 bg-gray-50 px-4 py-14">
        <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-3">
          <div className="rounded-3xl border border-gray-200 bg-white p-7">
            <h3 className="text-xl font-bold text-gray-950">MySQL-first backend</h3>
            <p className="mt-2 text-sm text-gray-600">No Docker required. Create the database locally, run the setup SQL once, then let FastAPI create the application tables.</p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white p-7">
            <h3 className="text-xl font-bold text-gray-950">Yelp API import</h3>
            <p className="mt-2 text-sm text-gray-600">Pull restaurant data, photos, hours, and available Yelp review snippets into MySQL for fast search and filtering.</p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white p-7">
            <h3 className="text-xl font-bold text-gray-950">Owner dashboard</h3>
            <p className="mt-2 text-sm text-gray-600">Owners can claim restaurants, review analytics, and update their restaurant metadata from one place.</p>
            <div className="mt-4">
              {user?.is_owner ? (
                <Link to="/owner" className="rounded-full bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700">Open owner dashboard</Link>
              ) : (
                <Link to="/signup" className="rounded-full bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700">Create owner account</Link>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
