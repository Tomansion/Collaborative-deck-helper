<template>
  <button class="card-tile" type="button" @click="$emit('open', card)">
    <span class="card-tile__frame">
      <img
        v-if="card.current_image"
        class="card-tile__photo"
        :src="card.current_image.url"
        :alt="card.label"
        loading="lazy"
      />
      <span v-else class="card-tile__placeholder">
        <span>＋</span>
        <span class="card-tile__placeholder-text">Ajouter une photo</span>
      </span>
      <img class="card-tile__overlay" :src="card.overlay_url" :alt="''" loading="lazy" />
    </span>
    <span class="card-tile__caption">
      <span class="card-tile__label">{{ card.label }}</span>
      <span v-if="card.description" class="card-tile__description">{{ card.description }}</span>
    </span>
  </button>
</template>

<script>
export default {
  name: 'CardTile',
  props: {
    card: { type: Object, required: true },
  },
  emits: ['open'],
}
</script>
