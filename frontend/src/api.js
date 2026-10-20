// Thin fetch wrapper around the backend REST API. Centralized here so
// error handling (French-friendly messages) stays consistent.

async function request(path, options = {}) {
  const res = await fetch(path, options)
  if (!res.ok) {
    let detail = `Erreur ${res.status}`
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  getDeck() {
    return request('/api/deck')
  },
  getCard(cardId) {
    return request(`/api/cards/${cardId}`)
  },
  getHistory(limit = 200) {
    return request(`/api/history?limit=${limit}`)
  },
  updateDescription(cardId, description) {
    return request(`/api/cards/${cardId}/description`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    })
  },
  uploadImage(cardId, file) {
    const formData = new FormData()
    formData.append('file', file)
    return request(`/api/cards/${cardId}/images`, {
      method: 'POST',
      body: formData,
    })
  },
  activateImage(cardId, imageId) {
    return request(`/api/cards/${cardId}/images/${imageId}/activate`, {
      method: 'PUT',
    })
  },
  deleteImage(cardId, imageId) {
    return request(`/api/cards/${cardId}/images/${imageId}`, {
      method: 'DELETE',
    })
  },
  exportZipUrl(includeMissing = false) {
    return `/api/export/zip${includeMissing ? '?include_missing=true' : ''}`
  },
}
