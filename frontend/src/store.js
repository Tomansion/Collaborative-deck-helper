// Shared reactive application state. Plain module (not Pinia): small
// enough app that a single reactive object, imported into each Options
// API component's data(), is simpler than adding a state-management
// dependency. Components read `this.store.*` and call the methods below
// to mutate it; the WebSocket client also writes into this object so
// every connected tab stays in sync automatically.
import { reactive } from 'vue'
import { api } from './api.js'

export const store = reactive({
  suits: [],
  values: [],
  cards: [],
  history: [],
  loading: true,
  error: null,
  wsConnected: false,
})

export function cardsBySuit(suitCode) {
  return store.cards.filter((c) => c.suit === suitCode)
}

export function jokerCards() {
  return store.cards.filter((c) => c.value === 'JOKER')
}

function upsertCard(card) {
  const index = store.cards.findIndex((c) => c.id === card.id)
  if (index === -1) {
    store.cards.push(card)
  } else {
    store.cards[index] = { ...store.cards[index], ...card }
  }
}

function prependHistory(entry) {
  if (store.history.some((e) => e.id === entry.id)) return
  store.history.unshift(entry)
}

export async function loadDeck() {
  store.loading = true
  store.error = null
  try {
    const deck = await api.getDeck()
    store.suits = deck.suits
    store.values = deck.values
    store.cards = deck.cards
  } catch (err) {
    store.error = err.message
  } finally {
    store.loading = false
  }
}

export async function loadHistory() {
  try {
    store.history = await api.getHistory()
  } catch (err) {
    store.error = err.message
  }
}

export async function updateDescription(cardId, description) {
  const card = await api.updateDescription(cardId, description)
  upsertCard(card)
  return card
}

export async function uploadImage(cardId, file) {
  const card = await api.uploadImage(cardId, file)
  upsertCard(card)
  return card
}

export async function activateImage(cardId, imageId) {
  const card = await api.activateImage(cardId, imageId)
  upsertCard(card)
  return card
}

export async function deleteImage(cardId, imageId) {
  const card = await api.deleteImage(cardId, imageId)
  upsertCard(card)
  return card
}

export function applyRealtimeMessage(message) {
  if (message.type === 'card_updated') {
    upsertCard(message.card)
    if (message.history_entry) prependHistory(message.history_entry)
  }
}
