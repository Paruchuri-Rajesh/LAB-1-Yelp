import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getRestaurant } from "../../api/restaurantApi";
import { getRestaurantReviews, deleteReview } from "../../api/reviewApi";
import { addFavorite, removeFavorite, checkFavoriteStatus } from "../../api/favoriteApi";
import { useAuth } from "../../context/AuthContext";
import StarRating from "../../components/StarRating";
import ReviewCard from "../../components/ReviewCard";
import { FaHeart, FaRegHeart, FaMapMarkerAlt, FaPhone, FaClock } from "react-icons/fa";

export default function RestaurantDetailPage() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [restaurant, setRestaurant] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [isFav, setIsFav] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [resRes, revRes] = await Promise.all([
          getRestaurant(id),
          getRestaurantReviews(id),
        ]);
        setRestaurant(resRes.data);
        setReviews(revRes.data);

        if (isAuthenticated) {
          try {
            const favRes = await checkFavoriteStatus(id);
            setIsFav(favRes.data.is_favorited);
          } catch {}
        }
      } catch {
        setRestaurant(null);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, isAuthenticated]);

  const toggleFavorite = async () => {
    if (!isAuthenticated) return navigate("/login");
    try {
      if (isFav) {
        await removeFavorite(id);
        setIsFav(false);
      } else {
        await addFavorite(id);
        setIsFav(true);
      }
    } catch {}
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm("Delete this review?")) return;
    try {
      await deleteReview(reviewId);
      setReviews(reviews.filter((r) => r.id !== reviewId));
    } catch {}
  };

  const handleEditReview = (review) => {
    navigate(`/restaurants/${id}/review/${review.id}`);
  };

  if (loading) return <div className="text-center py-10 text-xl">Loading...</div>;
  if (!restaurant) return <div className="text-center py-10 text-xl text-red-600">Restaurant not found</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Photo Gallery */}
      {restaurant.photos && restaurant.photos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-6 rounded-lg overflow-hidden">
          <img
            src={`http://localhost:8000${restaurant.photos[0]}`}
            alt={restaurant.name}
            className="w-full h-64 md:h-80 object-cover md:col-span-2"
          />
          <div className="hidden md:grid grid-rows-2 gap-2">
            {restaurant.photos.slice(1, 3).map((p, i) => (
              <img key={i} src={`http://localhost:8000${p}`} alt="" className="w-full h-full object-cover" />
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-gray-200 h-64 rounded-lg mb-6 flex items-center justify-center text-gray-500 text-xl">
          No photos available
        </div>
      )}

      {/* Restaurant Info */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h1 className="text-3xl font-bold">{restaurant.name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <StarRating rating={Math.round(restaurant.avg_rating || 0)} />
            <span className="text-gray-600">
              {restaurant.avg_rating ? restaurant.avg_rating.toFixed(1) : "No ratings"} ({restaurant.review_count} reviews)
            </span>
          </div>
          <div className="flex items-center gap-3 mt-2 text-gray-600">
            <span className="font-semibold">{restaurant.cuisine_type}</span>
            {restaurant.pricing_tier && (
              <>
                <span>·</span>
                <span className="text-green-700 font-semibold">{restaurant.pricing_tier}</span>
              </>
            )}
          </div>
        </div>
        <button onClick={toggleFavorite} className="bg-transparent border-none cursor-pointer p-2">
          {isFav ? <FaHeart size={28} color="#d32323" /> : <FaRegHeart size={28} color="#d32323" />}
        </button>
      </div>

      {/* Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="md:col-span-2">
          {restaurant.description && (
            <div className="mb-4">
              <h3 className="font-semibold text-lg mb-2">About</h3>
              <p className="text-gray-700">{restaurant.description}</p>
            </div>
          )}
          {restaurant.amenities && restaurant.amenities.length > 0 && (
            <div className="mb-4">
              <h3 className="font-semibold text-lg mb-2">Amenities</h3>
              <div className="flex flex-wrap gap-2">
                {restaurant.amenities.map((a, i) => (
                  <span key={i} className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-700">{a}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-2">
            <FaMapMarkerAlt className="mt-1 text-gray-500" />
            <span className="text-gray-700">{restaurant.address}, {restaurant.city} {restaurant.zip_code || ""}</span>
          </div>
          {restaurant.contact_info && (
            <div className="flex items-center gap-2">
              <FaPhone className="text-gray-500" />
              <span className="text-gray-700">{restaurant.contact_info}</span>
            </div>
          )}
          {restaurant.hours && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <FaClock className="text-gray-500" />
                <span className="font-semibold text-gray-700">Hours</span>
              </div>
              <div className="text-sm text-gray-600 ml-6">
                {Object.entries(restaurant.hours).map(([day, time]) => (
                  <div key={day} className="flex justify-between">
                    <span className="capitalize">{day}</span>
                    <span>{time}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reviews Section */}
      <div className="border-t pt-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Reviews ({restaurant.review_count})</h2>
          {isAuthenticated && (
            <Link
              to={`/restaurants/${id}/review`}
              className="px-6 py-2 text-white rounded-md font-semibold no-underline hover:opacity-90"
              style={{ backgroundColor: "#d32323" }}
            >
              Write a Review
            </Link>
          )}
        </div>

        {reviews.length === 0 ? (
          <p className="text-gray-500 py-4">No reviews yet. Be the first to review!</p>
        ) : (
          reviews.map((r) => (
            <ReviewCard key={r.id} review={r} onEdit={handleEditReview} onDelete={handleDeleteReview} />
          ))
        )}
      </div>
    </div>
  );
}
