<template>
  <header class="app-header">
    <div class="app-header__title">
      <span class="app-header__crown">♛</span>
      <div>
        <h1>Les Cinq Rois — notre deck à personnaliser</h1>
        <p class="app-header__subtitle">
          Un jeu de cartes fait main, pour un cadeau unique
        </p>
      </div>
    </div>

    <details class="app-header__intro" open>
      <summary>Comment ça marche ?</summary>
      <div class="app-header__intro-body">
        <p>
          Cette application nous permet de créer ensemble une version custom des
          Cinq Rois (55 cartes de 3 à Roi dans 5 couleurs, plus 6 jokers), à
          offrir en cadeau.
        </p>
        <ul>
          <li>
            Chaque carte a une image, Judith à fait une proposition que l'on
            peut voir en tant que description.
          </li>
          <li>
            Le deck est partagé : vos modifications apparaissent instantanément
            chez tout le monde. N'hésitez pas à ajouter vos photos et à changer
            les descriptions. Disons que vous êtes responsables de votre branche
            et que l'on fait la branche de Paton et Manon ensemble
          </li>
          <li>
            Si vous changez une image, l'ancienne reste disponible : vous pouvez
            revenir dessus à tout moment depuis la fiche de la carte.
          </li>
        </ul>
      </div>
    </details>

    <div class="app-header__actions">
      <span class="ws-indicator" :class="{ 'ws-indicator--on': connected }">
      </span>
      <span v-if="cardCount" class="progress-indicator">
        {{ photoCount }} / {{ cardCount }} cartes avec photo
      </span>
      <button
        class="btn btn--ghost"
        type="button"
        @click="$emit('show-history')"
      >
        Historique
      </button>
      <button class="btn btn--primary" type="button" @click="$emit('download')">
        ⬇ Télécharger le deck
      </button>
    </div>
  </header>
</template>

<script>
export default {
  name: "AppHeader",
  props: {
    connected: { type: Boolean, default: false },
    photoCount: { type: Number, default: 0 },
    cardCount: { type: Number, default: 0 },
  },
  emits: ["show-history", "download"],
};
</script>
