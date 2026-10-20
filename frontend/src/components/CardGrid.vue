<template>
  <div class="card-grid">
    <section v-for="suit in suits" :key="suit.code" class="card-group">
      <h2 class="card-group__title" :style="{ '--suit-color': suit.color }">
        <span class="card-group__symbol">{{ suit.symbol }}</span>
        {{ suit.label }}
      </h2>
      <div class="card-group__row">
        <CardTile
          v-for="card in cardsBySuit(suit.code)"
          :key="card.id"
          :card="card"
          @open="$emit('open-card', card)"
        />
      </div>
    </section>

    <section v-if="jokerCards.length" class="card-group">
      <h2 class="card-group__title" style="--suit-color: #2e8b3d">
        <span class="card-group__symbol">★</span>
        Jokers
      </h2>
      <div class="card-group__row">
        <CardTile
          v-for="card in jokerCards"
          :key="card.id"
          :card="card"
          @open="$emit('open-card', card)"
        />
      </div>
    </section>
  </div>
</template>

<script>
import CardTile from './CardTile.vue'

export default {
  name: 'CardGrid',
  components: { CardTile },
  props: {
    suits: { type: Array, required: true },
    cards: { type: Array, required: true },
  },
  emits: ['open-card'],
  computed: {
    jokerCards() {
      return this.cards.filter((c) => c.value === 'JOKER')
    },
  },
  methods: {
    cardsBySuit(suitCode) {
      return this.cards.filter((c) => c.suit === suitCode)
    },
  },
}
</script>
