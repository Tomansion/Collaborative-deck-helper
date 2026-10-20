// WebSocket client: keeps the shared deck in sync across every connected
// browser. Reconnects automatically with a short backoff if the
// connection drops (e.g. backend restart).
import { store, applyRealtimeMessage } from './store.js'

let socket = null
let reconnectDelay = 1000
const MAX_RECONNECT_DELAY = 10000

function wsUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/deck`
}

export function connectWebSocket() {
  socket = new WebSocket(wsUrl())

  socket.addEventListener('open', () => {
    store.wsConnected = true
    reconnectDelay = 1000
  })

  socket.addEventListener('message', (event) => {
    try {
      const message = JSON.parse(event.data)
      applyRealtimeMessage(message)
    } catch (err) {
      console.error('Message WebSocket invalide', err)
    }
  })

  socket.addEventListener('close', () => {
    store.wsConnected = false
    setTimeout(connectWebSocket, reconnectDelay)
    reconnectDelay = Math.min(reconnectDelay * 1.5, MAX_RECONNECT_DELAY)
  })

  socket.addEventListener('error', () => {
    socket.close()
  })
}
