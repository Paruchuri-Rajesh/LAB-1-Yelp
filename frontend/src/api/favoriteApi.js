import API from "./axios";

export const addFavorite = (restaurantId) =>
  API.post(`/favorites/${restaurantId}`);
export const removeFavorite = (restaurantId) =>
  API.delete(`/favorites/${restaurantId}`);
export const getFavorites = () => API.get("/favorites");
export const checkFavoriteStatus = (restaurantId) =>
  API.get(`/favorites/${restaurantId}/status`);
