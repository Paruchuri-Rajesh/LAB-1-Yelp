import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { createReview, updateReview, getRestaurantReviews } from "../../api/reviewApi";
import { getRestaurant } from "../../api/restaurantApi";
import StarRating from "../../components/StarRating";

export default function WriteReviewPage() {
  const { id: restaurantId, reviewId } = useParams();
  const navigate = useNavigate();
  const [restaurant, setRestaurant] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const isEdit = !!reviewId;

  useEffect(() => {
    getRestaurant(restaurantId).then((res) => setRestaurant(res.data));

    if (isEdit) {
      getRestaurantReviews(restaurantId).then((res) => {
        const review = res.data.find((r) => r.id === parseInt(reviewId));
        if (review) {
          setRating(review.rating);
          setComment(review.comment);
        }
      });
    }
  }, [restaurantId, reviewId, isEdit]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (rating === 0) {
      setError("Please select a rating");
      return;
    }
    setError("");
    setLoading(true);
    try {
      if (isEdit) {
        await updateReview(reviewId, { rating, comment });
      } else {
        await createReview({ restaurant_id: parseInt(restaurantId), rating, comment });
      }
      navigate(`/restaurants/${restaurantId}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit review");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">{isEdit ? "Edit Review" : "Write a Review"}</h1>
      {restaurant && <p className="text-gray-600 mb-6">for <strong>{restaurant.name}</strong></p>}

      {error && <div className="bg-red-100 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        <div>
          <label className="block text-lg font-semibold mb-2">Your Rating</label>
          <StarRating rating={rating} onRate={setRating} size={32} />
          {rating > 0 && (
            <p className="text-gray-600 mt-1">
              {["", "Not good", "Could be better", "OK", "Good", "Great"][rating]}
            </p>
          )}
        </div>

        <div>
          <label className="block text-lg font-semibold mb-2">Your Review</label>
          <textarea
            value={comment} onChange={(e) => setComment(e.target.value)} required rows={5}
            placeholder="Share your experience at this restaurant..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={loading}
            className="px-8 py-3 text-white rounded-md font-semibold hover:opacity-90 disabled:opacity-50 border-none cursor-pointer"
            style={{ backgroundColor: "#d32323" }}>
            {loading ? "Submitting..." : isEdit ? "Update Review" : "Submit Review"}
          </button>
          <button type="button" onClick={() => navigate(`/restaurants/${restaurantId}`)}
            className="px-8 py-3 bg-gray-200 rounded-md font-semibold border-none cursor-pointer">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
