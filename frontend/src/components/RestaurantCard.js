import { Link } from "react-router-dom";
import StarRating from "./StarRating";

export default function RestaurantCard({ restaurant }) {
  const photo =
    restaurant.photos && restaurant.photos.length > 0
      ? `http://localhost:8000${restaurant.photos[0]}`
      : "https://via.placeholder.com/400x250?text=No+Image";

  return (
    <Link
      to={`/restaurants/${restaurant.id}`}
      className="no-underline text-gray-800"
    >
      <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow duration-300">
        <img
          src={photo}
          alt={restaurant.name}
          className="w-full h-48 object-cover"
        />
        <div className="p-4">
          <h3 className="text-lg font-bold mb-1">{restaurant.name}</h3>
          <div className="flex items-center gap-2 mb-2">
            <StarRating rating={Math.round(restaurant.avg_rating || 0)} size={16} />
            <span className="text-sm text-gray-500">
              ({restaurant.review_count} reviews)
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>{restaurant.cuisine_type}</span>
            {restaurant.pricing_tier && (
              <>
                <span>·</span>
                <span className="text-green-700 font-semibold">
                  {restaurant.pricing_tier}
                </span>
              </>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {restaurant.city}
            {restaurant.zip_code ? `, ${restaurant.zip_code}` : ""}
          </p>
        </div>
      </div>
    </Link>
  );
}
