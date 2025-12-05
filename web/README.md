# Application carte & recherche POI (React + TypeScript + Vite)

Application front-end avec Vite + React + TypeScript pour rechercher des points d’intérêt, afficher une carte OpenStreetMap et un tableau triable/exportable.

## Démarrage

```bash
cd web
npm install        # déjà fait une première fois
npm run dev        # démarre le serveur avec HMR
npm run build      # build de production
```

## Fonctionnalités

- Champ adresse avec suggestions (API Adresse data.gouv).
- Sélecteur de rayon (0.1 km → 70 km) synchronisé slider + input.
- Champ mots-clés avec suggestions NAF depuis `http://127.0.0.1/get_nafs_suggestion` (fallback de démo si indisponible). Les mots-clés choisis sont affichés en “chips” supprimables.
- Bouton Rechercher : POST vers `http://127.0.0.1/search_pois` avec `{ address, radiusKm, keywords }`. En cas d’échec, des données mock sont affichées.
- Carte OpenStreetMap avec cercle de rayon et marqueurs cliquables.
- Tableau triable sur chaque colonne avec export CSV/Excel.

## Brancher vos API

- Suggestions NAF : implémenter `GET http://127.0.0.1/get_nafs_suggestion?query=...` qui renvoie `{ suggestions: [{ id, label }] }`.
- Recherche POI : implémenter `POST http://127.0.0.1/search_pois` qui renvoie `{ pois: [{ id, nom, lat, long, desc, site, num, mail, adresse, siret, siren, date, other1, other2 }] }`.

En l’absence de backend, l’application reste utilisable grâce aux données de démonstration.
