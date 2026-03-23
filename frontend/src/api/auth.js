import client from './client'

export const signup = (data) => client.post('/auth/signup', data)
export const login = (data) => client.post('/auth/login', data)
