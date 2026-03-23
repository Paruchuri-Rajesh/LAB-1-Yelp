import client from './client'

export const getMe = () => client.get('/users/me')
export const updateMe = (data) => client.put('/users/me', data)
export const uploadAvatar = (file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/users/me/avatar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const deleteAvatar = () => client.delete('/users/me/avatar')
export const getPreferences = () => client.get('/users/me/preferences')
export const updatePreferences = (data) => client.put('/users/me/preferences', data)
export const getMyReviews = (page = 1) => client.get('/users/me/reviews', { params: { page } })
