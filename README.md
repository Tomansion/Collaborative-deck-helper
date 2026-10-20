# Les Cinq Rois — Collaborative Deck Helper

Une petite application web pour préparer, à plusieurs, un jeu de cartes
personnalisé (inspiré du jeu des **Cinq Rois** / *Five Crowns* : 55 cartes de
3 à Roi dans 5 couleurs, plus 6 jokers) destiné à être imprimé et offert en
cadeau.

Chaque carte a une image et une description, modifiables par n'importe qui :
le deck est partagé, les changements se propagent en direct à tous les
navigateurs connectés (WebSocket), l'historique des images d'une carte est
conservé (on peut revenir en arrière), et tout l'historique des modifications
est consultable. Une fois le deck prêt, on télécharge un zip avec, pour
chaque carte, la photo choisie fusionnée avec l'habillage coloré de sa
couleur/valeur, prêt à imprimer.

Voir [`Spec.md`](Spec.md) pour la spécification complète.

## Architecture

- **Backend** : FastAPI + SQLAlchemy + SQLite (`backend/`). Sert aussi
  l'API WebSocket (`/ws/deck`) utilisée pour la synchronisation temps réel,
  et génère les habillages colorés des cartes avec Pillow.
- **Frontend** : Vue 3 (Options API) + Vite (`frontend/`).
- **Images** : enregistrées sur disque (dossier `uploads/`), leur chemin est
  stocké en base ; l'image "courante" d'une carte et son historique sont
  tous deux conservés.
- **Descriptions par défaut** : [`default_description.md`](default_description.md)
  pré-remplit la description de chaque carte au premier démarrage (une
  description déjà modifiée depuis l'app n'est jamais écrasée). Ce fichier
  est généré depuis [`Default_descriptions.ods`](Default_descriptions.ods)
  (plus pratique à éditer à plusieurs) via
  `python3 scripts/ods_to_default_descriptions.py`.

## Développement

Prérequis : Python 3.10+, Node 20+.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

L'API écoute sur `http://localhost:8000` (`/api/...`, `/ws/deck`). La base
SQLite et les images uploadées sont stockées dans `backend/data/` (créé
automatiquement, ignoré par git).

### Frontend

Dans un second terminal :

```bash
cd frontend
npm install
npm run dev
```

L'app est servie sur `http://localhost:5173` ; le serveur de dev Vite
redirige `/api`, `/uploads` et `/ws` vers le backend sur le port 8000 (voir
`frontend/vite.config.js`). Ouvrez `http://localhost:5173`.

### Mettre à jour les descriptions par défaut

Après avoir modifié `Default_descriptions.ods` :

```bash
python3 scripts/ods_to_default_descriptions.py
```

Cela régénère `default_description.md`. Le backend applique ensuite ces
valeurs par défaut à chaque démarrage, uniquement sur les cartes dont la
description n'a encore jamais été modifiée depuis l'application.

## Production (Docker)

Un unique `Dockerfile` multi-étapes construit le frontend puis l'embarque
dans l'image du backend, qui sert à la fois l'API et les fichiers statiques
du frontend.

```bash
docker compose up --build
```

ou, sans compose :

```bash
docker build -t deck-helper .
docker run -d -p 8000:8000 -v deck_data:/data --name deck-helper deck-helper
```

L'application est alors disponible sur `http://localhost:8000`. Le volume
`/data` contient la base SQLite et les images uploadées : il doit être
persisté (volume nommé ou bind mount) pour ne pas perdre le deck entre deux
déploiements.

### Variables d'environnement (optionnelles)

| Variable                     | Par défaut                          | Usage                                   |
|-------------------------------|--------------------------------------|------------------------------------------|
| `DECK_DATA_DIR`               | `/data` (Docker) / `backend/data`    | Dossier de la base SQLite + des images   |
| `DECK_DEFAULT_DESCRIPTIONS`   | `/app/default_description.md`        | Chemin du fichier de descriptions par défaut |
| `DECK_FRONTEND_DIST`          | `/app/frontend_dist`                 | Dossier du build frontend à servir       |

## Structure du dépôt

```
backend/            API FastAPI (modèles, routes, génération des overlays)
frontend/            App Vue 3 (Options API)
scripts/              Utilitaires de dev (conversion .ods -> .md)
reference-images/    Visuels de référence pour le rendu des cartes
Spec.md               Spécification de l'application
default_description.md       Descriptions par défaut (généré, voir ci-dessus)
Default_descriptions.ods     Source éditable des descriptions par défaut
Dockerfile, docker-compose.yml   Build/déploiement en production
```
