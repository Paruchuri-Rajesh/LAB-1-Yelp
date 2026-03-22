import API from "./axios";

export const searchRestaurants = (params) => API.get("/restaurants", { params });
export const getRestaurant = (id) => API.get(`/restaurants/${id}`);
export const createRestaurant = (data) => API.post("/restaurants", data);
export const updateRestaurant = (id, data) => API.put(`/restaurants/${id}`, data);
export const uploadRestaurantPhotos = (id, files) => {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  return API.post(`/restaurants/${id}/photos`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
