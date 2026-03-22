import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { searchRestaurants } from "../../api/restaurantApi";
import RestaurantCard from "../../components/RestaurantCard";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [featured, setFeatured] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    searchRestaurants({ limit: 6 })
      .then((res) => setFeatured(res.data))
      .catch(() => {});
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query) params.set("keyword", query);
    if (location) params.set("city", location);
    navigate(`/search?${params.toString()}`);
  };

  return (
    <div>
      {/* Hero Section */}
      <div
        className="text-white py-24 px-4"
        style={{
          background: "linear-gradient(135deg, #d32323 0%, #af1c1c 100%)",
        }}
      >
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold mb-4">Find Your Next Favorite Restaurant</h1>
          <p className="text-xl mb-8 opacity-90">
            Discover, review, and share the best dining experiences
          </p>

          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-3 max-w-2xl mx-auto">
            <input
              type="text"
              placeholder="Search restaurants, cuisines, keywords..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 px-4 py-3 rounded-md text-gray-800 text-lg focus:outline-none"
            />
            <input
              type="text"
              placeholder="City or Zip"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="md:w-48 px-4 py-3 rounded-md text-gray-800 text-lg focus:outline-none"
            />
            <button
              type="submit"
              className="px-8 py-3 bg-gray-900 text-white rounded-md text-lg font-semibold hover:bg-gray-800 border-none cursor-pointer"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {/* Featured Restaurants */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold mb-6">Recently Added Restaurants</h2>
        {featured.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No restaurants yet. Be the first to add one!
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featured.map((r) => (
              <RestaurantCard key={r.id} restaurant={r} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
