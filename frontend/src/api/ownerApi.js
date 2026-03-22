import API from "./axios";

export const getOwnerDashboard = () => API.get("/owner/dashboard");
export const getOwnerRestaurants = () => API.get("/owner/restaurants");
export const claimRestaurant = (id) => API.post(`/owner/claim/${id}`);
export const getOwnerRestaurantReviews = (id) =>
  API.get(`/owner/restaurants/${id}/reviews`);
