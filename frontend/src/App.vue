<template>
  <div class="app">
    <AppHeader
      :connected="store.wsConnected"
      @show-history="showHistory = true"
      @download="downloadZip"
    />

    <main class="app__main">
      <p v-if="store.loading" class="app__status">Chargement du deck…</p>
      <p v-else-if="store.error" class="app__status app__status--error">{{ store.error }}</p>
      <CardGrid
        v-else
        :suits="store.suits"
        :cards="store.cards"
        @open-card="openCard"
      />
    </main>

    <CardModal v-if="selectedCardId !== null" :card-id="selectedCardId" @close="selectedCardId = null" />
    <HistoryPanel v-if="showHistory" :entries="store.history" @close="showHistory = false" />
  </div>
</template>

<script>
import AppHeader from './components/AppHeader.vue'
import CardGrid from './components/CardGrid.vue'
import CardModal from './components/CardModal.vue'
import HistoryPanel from './components/HistoryPanel.vue'
import { store, loadDeck, loadHistory } from './store.js'
import { connectWebSocket } from './ws.js'
import { api } from './api.js'

export default {
  name: 'App',
  components: { AppHeader, CardGrid, CardModal, HistoryPanel },
  data() {
    return {
      store,
      selectedCardId: null,
      showHistory: false,
    }
  },
  created() {
    loadDeck()
    loadHistory()
    connectWebSocket()
  },
  methods: {
    openCard(card) {
      this.selectedCardId = card.id
    },
    downloadZip() {
      window.location.href = api.exportZipUrl()
    },
  },
}
</script>
