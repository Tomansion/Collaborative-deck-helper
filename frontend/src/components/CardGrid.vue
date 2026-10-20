<template>
  <div class="card-table">
    <div class="card-table__scroll">
      <div class="card-table__header">
        <span class="card-table__row-label"></span>
        <span
          v-for="suit in suits"
          :key="suit.code"
          class="card-table__header-cell"
          :style="{ '--suit-color': suit.color }"
        >
          <span class="card-table__header-symbol">{{ suit.symbol }}</span>
          {{ suit.label }}
        </span>
      </div>

      <div v-for="value in values" :key="value" class="card-table__row">
        <span class="card-table__row-label">{{ value }}</span>
        <CardTile
          v-for="suit in suits"
          :key="suit.code + value"
          :card="cardFor(suit.code, value)"
          @open="$emit('open-card', $event)"
        />
      </div>
    </div>

    <section v-if="jokerCards.length" class="card-group card-group--jokers">
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
    values: { type: Array, required: true },
    cards: { type: Array, required: true },
  },
  emits: ['open-card'],
  computed: {
    jokerCards() {
      return this.cards.filter((c) => c.value === 'JOKER')
    },
  },
  methods: {
    cardFor(suitCode, value) {
      return this.cards.find((c) => c.suit === suitCode && c.value === value)
    },
  },
}
</script>
