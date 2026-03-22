import API from "./axios";

export const getProfile = () => API.get("/users/profile");
export const updateProfile = (data) => API.put("/users/profile", data);
export const uploadProfilePicture = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/users/profile-picture", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
export const getPreferences = () => API.get("/users/preferences");
export const updatePreferences = (data) => API.put("/users/preferences", data);
export const getUserReviews = () => API.get("/users/reviews");
