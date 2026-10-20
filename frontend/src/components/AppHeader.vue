<template>
  <header class="app-header">
    <div class="app-header__title">
      <span class="app-header__crown">♛</span>
      <div>
        <h1>Les Cinq Rois — notre deck à personnaliser</h1>
        <p class="app-header__subtitle">Un jeu de cartes fait main, pour un cadeau unique</p>
      </div>
    </div>

    <details class="app-header__intro" open>
      <summary>Comment ça marche ?</summary>
      <div class="app-header__intro-body">
        <p>
          Cette application nous permet de préparer ensemble un vrai jeu de
          cartes personnalisé (inspiré du jeu des <strong>Cinq Rois</strong>,
          55 cartes de 3 à Roi dans 5 couleurs, plus 6 jokers), à offrir en
          cadeau.
        </p>
        <ul>
          <li>
            Chaque carte a une <strong>image</strong> et une <strong>description</strong>
            que vous pouvez modifier librement.
          </li>
          <li>
            Le deck est <strong>partagé</strong> : vos modifications
            apparaissent instantanément chez tout le monde, et chaque
            changement est gardé dans l'historique.
          </li>
          <li>
            Si vous changez une image, l'ancienne reste disponible : vous
            pouvez revenir dessus à tout moment depuis la fiche de la carte.
          </li>
          <li>
            Une fois satisfait·e du résultat, téléchargez le
            <strong>zip</strong> prêt à imprimer depuis le bouton en haut à
            droite.
          </li>
        </ul>
      </div>
    </details>

    <div class="app-header__actions">
      <span class="ws-indicator" :class="{ 'ws-indicator--on': connected }">
        <span class="ws-indicator__dot"></span>
        {{ connected ? 'Connecté en direct' : 'Connexion…' }}
      </span>
      <span v-if="cardCount" class="progress-indicator">
        {{ photoCount }} / {{ cardCount }} cartes avec photo
      </span>
      <button class="btn btn--ghost" type="button" @click="$emit('show-history')">
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
  name: 'AppHeader',
  props: {
    connected: { type: Boolean, default: false },
    photoCount: { type: Number, default: 0 },
    cardCount: { type: Number, default: 0 },
  },
  emits: ['show-history', 'download'],
}
</script>
