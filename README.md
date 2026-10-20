# Les Cinq Rois — Collaborative Deck Helper

A small web app for preparing a personalized deck of cards together,
inspired by the **Cinq Rois** / *Five Crowns* game (55 cards from 3 to King
in 5 colors, plus 6 jokers), meant to be printed and given as a gift.

Each card has an image and a description, editable by anyone: the deck is
shared, changes propagate live to every connected browser (WebSocket), a
card's image history is kept (you can revert to a previous one), and the
full change history is browsable. Once the deck is ready, download a zip
with, for each card, the chosen photo merged with its color/value overlay,
ready to print.

See [`Spec.md`](Spec.md) for the full specification. The app's UI and all
card content are in French (per the spec); this README is in English.

## Architecture

- **Backend**: FastAPI + SQLAlchemy + SQLite (`backend/`). Also serves the
  WebSocket API (`/ws/deck`) used for realtime sync, and generates the
  colored card overlays with Pillow.
- **Frontend**: Vue 3 (Options API) + Vite (`frontend/`).
- **Images**: stored on disk (`uploads/` folder), their path stored in the
  DB; a card's "current" image and its full history are both kept.
- **Default descriptions**: [`default_description.md`](default_description.md)
  pre-fills every card's description on first boot (a description already
  edited from the app is never overwritten). It's the source of truth and
  can be edited directly. It was originally filled in from a spreadsheet
  (`Default_descriptions.ods`, handier for editing with several people) via
  `scripts/ods_to_default_descriptions.py` — kept around in case that
  workflow is useful again, but not required to edit the file.

## Development

Prerequisites: Python 3.10+, Node 20+.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API listens on `http://localhost:8000` (`/api/...`, `/ws/deck`). The
SQLite database and uploaded images are stored in `backend/data/` (created
automatically, git-ignored).

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The app is served on `http://localhost:5173`; the Vite dev server proxies
`/api`, `/uploads` and `/ws` to the backend on port 8000 (see
`frontend/vite.config.js`). Open `http://localhost:5173`.

### Updating the default descriptions

Just edit `default_description.md` directly (format: a markdown table, one
row per value, one column per suit, plus a `## Jokers` section). The backend
applies these defaults on every startup, only to cards whose description
has never been edited from the app.

If you'd rather work from a spreadsheet (handy for editing with several
people), `python3 scripts/ods_to_default_descriptions.py [file.ods]`
regenerates `default_description.md` from an `.ods` file with the same
shape (one column per suit, one row per value).

## Production (Docker)

A single multi-stage `Dockerfile` builds the frontend and bundles it into
the backend image, which serves both the API and the frontend's static
files.

```bash
docker compose up --build
```

or, without compose:

```bash
docker build -t deck-helper .
docker run -d -p 8000:8000 -v deck_data:/data --name deck-helper deck-helper
```

The app is then available on `http://localhost:8000`. The `/data` volume
holds the SQLite database and uploaded images: it must be persisted (named
volume or bind mount) so the deck isn't lost between deployments.

### Environment variables (optional)

| Variable                     | Default                              | Purpose                                   |
|-------------------------------|--------------------------------------|--------------------------------------------|
| `DECK_DATA_DIR`               | `/data` (Docker) / `backend/data`    | Folder for the SQLite DB + images          |
| `DECK_DEFAULT_DESCRIPTIONS`   | `/app/default_description.md`        | Path to the default-descriptions file      |
| `DECK_FRONTEND_DIST`          | `/app/frontend_dist`                 | Folder of the built frontend to serve      |

## Repository structure

```
backend/            FastAPI API (models, routes, overlay generation)
frontend/            Vue 3 app (Options API)
scripts/              Dev utilities (.ods -> .md conversion, optional)
reference-images/    Reference visuals for the card rendering
Spec.md               Application specification
default_description.md       Default descriptions (edit directly)
Dockerfile, docker-compose.yml   Production build/deployment
```
