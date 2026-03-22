import StarRating from "./StarRating";
import { useAuth } from "../context/AuthContext";

export default function ReviewCard({ review, onEdit, onDelete }) {
  const { user } = useAuth();
  const isOwner = user && user.id === review.user_id;

  return (
    <div className="border-b border-gray-200 py-4">
      <div className="flex justify-between items-start">
        <div>
          <p className="font-semibold">{review.user_name}</p>
          <div className="flex items-center gap-2 mt-1">
            <StarRating rating={review.rating} size={14} />
            <span className="text-sm text-gray-500">
              {review.created_at
                ? new Date(review.created_at).toLocaleDateString()
                : ""}
            </span>
          </div>
        </div>
        {isOwner && (
          <div className="flex gap-2">
            <button
              onClick={() => onEdit && onEdit(review)}
              className="text-sm text-blue-600 hover:underline bg-transparent border-none cursor-pointer"
            >
              Edit
            </button>
            <button
              onClick={() => onDelete && onDelete(review.id)}
              className="text-sm text-red-600 hover:underline bg-transparent border-none cursor-pointer"
            >
              Delete
            </button>
          </div>
        )}
      </div>
      <p className="mt-2 text-gray-700">{review.comment}</p>
      {review.photos && review.photos.length > 0 && (
        <div className="flex gap-2 mt-2">
          {review.photos.map((photo, i) => (
            <img
              key={i}
              src={`http://localhost:8000${photo}`}
              alt="Review"
              className="w-20 h-20 object-cover rounded"
            />
          ))}
        </div>
      )}
    </div>
  );
}
