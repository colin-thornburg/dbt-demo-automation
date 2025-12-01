import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const createSession = async () => {
  const response = await api.post('/api/sessions')
  return response.data.session_id
}

export const getConfig = async (sessionId) => {
  const response = await api.get(`/api/sessions/${sessionId}/config`)
  return response.data
}

export const setDemoInputs = async (sessionId, inputs) => {
  await api.post(`/api/sessions/${sessionId}/demo-inputs`, inputs)
}

export const setAIConfig = async (sessionId, config) => {
  await api.post(`/api/sessions/${sessionId}/ai-config`, config)
}

export const setGitHubConfig = async (sessionId, config) => {
  await api.post(`/api/sessions/${sessionId}/github-config`, config)
}

export const setDbtConfig = async (sessionId, config) => {
  await api.post(`/api/sessions/${sessionId}/dbt-config`, config)
}

export const getStatus = async (sessionId) => {
  const response = await api.get(`/api/sessions/${sessionId}/status`)
  return response.data
}

export const getMissingFields = async (sessionId) => {
  const response = await api.get(`/api/sessions/${sessionId}/missing-fields`)
  return response.data
}

export const generateScenario = async (sessionId) => {
  const response = await api.post(`/api/sessions/${sessionId}/generate-scenario`)
  return response.data
}

export const getScenario = async (sessionId) => {
  const response = await api.get(`/api/sessions/${sessionId}/scenario`)
  return response.data
}

export const regenerateScenario = async (sessionId, feedback) => {
  const response = await api.post(`/api/sessions/${sessionId}/regenerate-scenario`, { feedback })
  return response.data
}

export const generateFiles = async (sessionId) => {
  await api.post(`/api/sessions/${sessionId}/generate-files`)
}

export const getFiles = async (sessionId) => {
  const response = await api.get(`/api/sessions/${sessionId}/files`)
  return response.data
}

export const createRepository = async (sessionId, repoName) => {
  const response = await api.post(`/api/sessions/${sessionId}/create-repository`, null, {
    params: { repo_name: repoName },
  })
  return response.data
}

export const getRepository = async (sessionId) => {
  const response = await api.get(`/api/sessions/${sessionId}/repository`)
  return response.data
}

export const provisionDbtCloud = async (sessionId) => {
  const response = await api.post(`/api/sessions/${sessionId}/provision-dbt-cloud`)
  return response.data
}

export const getProvisioningResult = async (sessionId) => {
  const response = await api.get(`/api/sessions/${sessionId}/provisioning`)
  return response.data
}

export const getProvisioningProgress = async (sessionId) => {
  const response = await api.get(`/api/sessions/${sessionId}/provisioning-progress`)
  return response.data
}

export default api

