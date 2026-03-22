import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getOwnerRestaurants } from "../../api/ownerApi";
import RestaurantCard from "../../components/RestaurantCard";

export default function OwnerRestaurantsPage() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOwnerRestaurants()
      .then((res) => setRestaurants(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-10">Loading...</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">My Restaurants</h1>
        <div className="flex gap-3">
          <Link to="/restaurants/add"
            className="px-6 py-2 text-white rounded-md font-semibold no-underline"
            style={{ backgroundColor: "#d32323" }}>
            Add Restaurant
          </Link>
          <Link to="/owner/claim"
            className="px-6 py-2 bg-gray-800 text-white rounded-md font-semibold no-underline">
            Claim Restaurant
          </Link>
        </div>
      </div>

      {restaurants.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No restaurants yet. Add or claim one!</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {restaurants.map((r) => (
            <RestaurantCard key={r.id} restaurant={r} />
          ))}
        </div>
      )}
    </div>
  );
}
