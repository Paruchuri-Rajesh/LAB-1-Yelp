import client from './client'

export const searchRestaurants = (params) => client.get('/restaurants', { params })
export const getRestaurant = (id) => client.get(`/restaurants/${id}`)
export const getReviews = (restaurantId, page = 1) =>
  client.get(`/restaurants/${restaurantId}/reviews`, { params: { page } })
export const createReview = (restaurantId, data) => client.post(`/restaurants/${restaurantId}/reviews`, data)
export const updateReview = (restaurantId, reviewId, data) =>
  client.put(`/restaurants/${restaurantId}/reviews/${reviewId}`, data)
export const deleteReview = (restaurantId, reviewId) =>
  client.delete(`/restaurants/${restaurantId}/reviews/${reviewId}`)
export const uploadReviewPhotos = (restaurantId, reviewId, formData) =>
  client.post(`/restaurants/${restaurantId}/reviews/${reviewId}/photos`, formData)
export const searchPlaces = (q) => client.get('/restaurants/places', { params: { q } })
export const importRestaurantsFromYelp = (data) => client.post('/restaurants/import/yelp', data)
export const suggestRestaurant = (formData) => client.post('/restaurants/suggest', formData)
