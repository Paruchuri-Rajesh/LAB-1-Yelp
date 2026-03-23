import client from './client'

export const chat = (payload) => client.post('/ai-assistant/chat', payload)
