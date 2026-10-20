<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal modal--history" role="dialog" aria-modal="true">
      <button class="modal__close" type="button" @click="$emit('close')" aria-label="Fermer">✕</button>
      <h2>Historique des modifications</h2>
      <p v-if="!entries.length" class="modal__hint">Aucune modification pour le moment.</p>
      <ul v-else class="history-list">
        <li v-for="entry in entries" :key="entry.id" class="history-list__item">
          <div>
            <p class="history-list__summary">{{ entry.summary }}</p>
            <p class="history-list__date">{{ formatDate(entry.created_at) }}</p>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
const formatter = new Intl.DateTimeFormat('fr-FR', {
  dateStyle: 'long',
  timeStyle: 'short',
})

export default {
  name: 'HistoryPanel',
  props: {
    entries: { type: Array, required: true },
  },
  emits: ['close'],
  methods: {
    formatDate(iso) {
      return formatter.format(new Date(iso))
    },
  },
}
</script>
