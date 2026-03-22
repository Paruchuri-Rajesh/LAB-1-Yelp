import { FaStar, FaRegStar } from "react-icons/fa";

export default function StarRating({ rating, onRate, size = 20 }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <span
          key={star}
          onClick={() => onRate && onRate(star)}
          className={onRate ? "cursor-pointer" : ""}
        >
          {star <= rating ? (
            <FaStar size={size} color="#d32323" />
          ) : (
            <FaRegStar size={size} color="#d32323" />
          )}
        </span>
      ))}
    </div>
  );
}
