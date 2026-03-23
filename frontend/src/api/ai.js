import client from './client'

export const chat = (payload) => client.post('/ai-assistant/chat', payload)
export const chatJson = (payload) => client.post('/ai-assistant/chat/json', payload)
export const chatStreamEndpoint = '/api/v1/ai-assistant/chat/stream'