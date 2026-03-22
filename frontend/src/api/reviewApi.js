import API from "./axios";

export const createReview = (data) => API.post("/reviews", data);
export const getRestaurantReviews = (restaurantId) =>
  API.get(`/restaurants/${restaurantId}/reviews`);
export const updateReview = (id, data) => API.put(`/reviews/${id}`, data);
export const deleteReview = (id) => API.delete(`/reviews/${id}`);
