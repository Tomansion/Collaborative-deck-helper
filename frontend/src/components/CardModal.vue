<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal" role="dialog" aria-modal="true">
      <button class="modal__close" type="button" @click="$emit('close')" aria-label="Fermer">✕</button>

      <div v-if="!detail" class="modal__loading">Chargement…</div>

      <template v-else>
        <div class="modal__visual">
          <span class="modal__preview">
            <img
              v-if="detail.current_image"
              class="modal__preview-photo"
              :src="detail.current_image.url"
              :alt="detail.label"
            />
            <span v-else class="modal__preview-placeholder">Pas encore de photo</span>
            <img class="modal__preview-overlay" :src="detail.overlay_url" alt="" />
          </span>
        </div>

        <div class="modal__panel">
          <div class="modal__panel-header">
            <h2>{{ detail.label }}</h2>
            <p class="modal__hint">Les modifications sont visibles par tout le monde instantanément.</p>
          </div>

          <section class="modal__section">
            <h3>Description</h3>
            <textarea
              v-model="descriptionDraft"
              class="modal__textarea"
              rows="3"
              placeholder="Ajoutez une description, une anecdote…"
              @input="scheduleSave"
              @blur="saveDescriptionNow"
            ></textarea>
            <p class="modal__save-status">
              <span v-if="saveState === 'saving'">Enregistrement…</span>
              <span v-else-if="saveState === 'saved'">Enregistré ✓</span>
              <span v-else-if="saveState === 'error'" class="modal__error">{{ saveError }}</span>
            </p>
          </section>

          <section class="modal__section">
            <h3>Photo</h3>
            <label
              class="modal__dropzone"
              :class="{ 'modal__dropzone--active': dragActive, 'modal__dropzone--busy': uploading }"
              @dragover.prevent="dragActive = true"
              @dragleave.prevent="dragActive = false"
              @drop.prevent="onDrop"
            >
              <input type="file" accept="image/*" class="modal__file-input" @change="onFileChange" />
              <span v-if="uploading">Envoi en cours…</span>
              <span v-else>Glissez une image ici, ou cliquez pour en choisir une</span>
            </label>
            <p v-if="uploadError" class="modal__error">{{ uploadError }}</p>
          </section>

          <section v-if="detail.images.length" class="modal__section">
            <h3>Historique des images ({{ detail.images.length }})</h3>
            <div class="modal__image-history">
              <button
                v-for="img in detail.images"
                :key="img.id"
                type="button"
                class="modal__history-thumb"
                :class="{ 'modal__history-thumb--current': img.is_current }"
                :disabled="img.is_current"
                @click="activate(img)"
                :title="img.is_current ? 'Image actuelle' : 'Revenir à cette image'"
              >
                <img :src="img.url" :alt="img.original_filename" />
                <span v-if="img.is_current" class="modal__history-badge">Actuelle</span>
              </button>
            </div>
          </section>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { api } from '../api.js'
import { store, updateDescription, uploadImage, activateImage } from '../store.js'

export default {
  name: 'CardModal',
  props: {
    cardId: { type: Number, required: true },
  },
  emits: ['close'],
  data() {
    return {
      detail: null,
      descriptionDraft: '',
      saveState: 'idle', // idle | saving | saved | error
      saveError: '',
      saveTimer: null,
      uploading: false,
      uploadError: '',
      dragActive: false,
    }
  },
  computed: {
    storeCard() {
      return store.cards.find((c) => c.id === this.cardId)
    },
  },
  watch: {
    cardId: {
      immediate: true,
      async handler() {
        this.detail = null
        this.saveState = 'idle'
        const detail = await api.getCard(this.cardId)
        this.detail = detail
        this.descriptionDraft = detail.description
      },
    },
    storeCard: {
      deep: true,
      handler(updated) {
        if (updated && updated.images && this.detail) {
          this.detail = { ...this.detail, ...updated }
        }
      },
    },
  },
  beforeUnmount() {
    if (this.saveTimer) clearTimeout(this.saveTimer)
  },
  methods: {
    scheduleSave() {
      this.saveState = 'idle'
      if (this.saveTimer) clearTimeout(this.saveTimer)
      this.saveTimer = setTimeout(() => this.saveDescriptionNow(), 800)
    },
    async saveDescriptionNow() {
      if (this.saveTimer) {
        clearTimeout(this.saveTimer)
        this.saveTimer = null
      }
      if (!this.detail || this.descriptionDraft === this.detail.description) return
      this.saveState = 'saving'
      try {
        const updated = await updateDescription(this.cardId, this.descriptionDraft)
        this.detail = { ...this.detail, ...updated }
        this.saveState = 'saved'
      } catch (err) {
        this.saveState = 'error'
        this.saveError = err.message
      }
    },
    async onFileChange(event) {
      const file = event.target.files?.[0]
      event.target.value = ''
      if (file) await this.doUpload(file)
    },
    async onDrop(event) {
      this.dragActive = false
      const file = event.dataTransfer?.files?.[0]
      if (file) await this.doUpload(file)
    },
    async doUpload(file) {
      this.uploading = true
      this.uploadError = ''
      try {
        const updated = await uploadImage(this.cardId, file)
        this.detail = { ...this.detail, ...updated }
      } catch (err) {
        this.uploadError = err.message
      } finally {
        this.uploading = false
      }
    },
    async activate(img) {
      if (img.is_current) return
      try {
        const updated = await activateImage(this.cardId, img.id)
        this.detail = { ...this.detail, ...updated }
      } catch (err) {
        this.uploadError = err.message
      }
    },
  },
}
</script>
