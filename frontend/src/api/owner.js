import client from './client'

export const claimRestaurant = (restaurantId) => client.post(`/owner/restaurants/${restaurantId}/claim`)
export const getOwnerDashboard = () => client.get('/owner/dashboard')
export const getOwnedRestaurants = () => client.get('/owner/restaurants')
export const getOwnerRestaurantDashboard = (restaurantId) =>
  client.get(`/owner/restaurants/${restaurantId}/dashboard`)
export const updateOwnedRestaurant = (restaurantId, data) =>
  client.put(`/owner/restaurants/${restaurantId}`, data)
export const createOwnedRestaurant = (formData) =>
  client.post(`/owner/restaurants`, formData)
export const uploadOwnedRestaurantPhotos = (restaurantId, formData) =>
  client.post(`/owner/restaurants/${restaurantId}/photos`, formData)
export const deleteOwnedRestaurantPhoto = (restaurantId, photoId) =>
  client.delete(`/owner/restaurants/${restaurantId}/photos/${photoId}`)
export const updateOwnedRestaurantHours = (restaurantId, data) =>
  client.put(`/owner/restaurants/${restaurantId}/hours`, data)
