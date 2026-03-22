import { useState, useEffect } from "react";
import { getOwnerDashboard } from "../../api/ownerApi";
import StarRating from "../../components/StarRating";

export default function OwnerDashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOwnerDashboard()
      .then((res) => setDashboard(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-10">Loading...</div>;
  if (!dashboard) return <div className="text-center py-10">Failed to load dashboard</div>;

  const maxCount = Math.max(...Object.values(dashboard.ratings_distribution), 1);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Owner Dashboard</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-3xl font-bold" style={{ color: "#d32323" }}>{dashboard.total_restaurants}</p>
          <p className="text-gray-600">Restaurants</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-3xl font-bold" style={{ color: "#d32323" }}>{dashboard.total_reviews}</p>
          <p className="text-gray-600">Total Reviews</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-3xl font-bold" style={{ color: "#d32323" }}>
            {dashboard.average_rating ? dashboard.average_rating.toFixed(1) : "N/A"}
          </p>
          <p className="text-gray-600">Average Rating</p>
        </div>
      </div>

      {/* Ratings Distribution */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">Ratings Distribution</h2>
        {[5, 4, 3, 2, 1].map((star) => (
          <div key={star} className="flex items-center gap-3 mb-2">
            <span className="w-8 text-sm font-medium">{star} star</span>
            <div className="flex-1 bg-gray-200 rounded-full h-4">
              <div
                className="h-4 rounded-full"
                style={{
                  width: `${(dashboard.ratings_distribution[star] / maxCount) * 100}%`,
                  backgroundColor: "#d32323",
                }}
              />
            </div>
            <span className="w-8 text-sm text-gray-600">{dashboard.ratings_distribution[star]}</span>
          </div>
        ))}
      </div>

      {/* Recent Reviews */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Recent Reviews</h2>
        {dashboard.recent_reviews.length === 0 ? (
          <p className="text-gray-500">No reviews yet.</p>
        ) : (
          dashboard.recent_reviews.map((r) => (
            <div key={r.id} className="border-b border-gray-100 py-3 last:border-b-0">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold">{r.user_name}</p>
                  <p className="text-sm text-gray-500">{r.restaurant_name}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StarRating rating={r.rating} size={14} />
                  <span className="text-sm text-gray-500">{r.created_at?.split("T")[0]}</span>
                </div>
              </div>
              <p className="text-gray-700 mt-1">{r.comment}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
