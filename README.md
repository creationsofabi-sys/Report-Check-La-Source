# La Source — Report Check

Prototype fonctionnel d'une base de vérification de rapports pour diamants et pierres précieuses, avec identité visuelle La Source.

## Fonctions incluses

- Recherche publique par numéro de rapport
- Fiche détaillée responsive et imprimable
- Gestion des diamants et des pierres précieuses
- Statuts : Actif, Suspendu, Archivé
- Administration : création, modification, suppression et filtrage
- Ajout d'une photographie et d'un PDF par rapport
- Base SQLite initialisée automatiquement
- Deux rapports de démonstration

## Installation locale

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate
# macOS / Linux : source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Puis ouvrir : `http://127.0.0.1:5000`

## Accès administrateur de démonstration

- Identifiant : `admin`
- Mot de passe : `2002`

### Sécurité avant mise en ligne

Définir impérativement des variables d'environnement :

```bash
LS_ADMIN_USER="votre-identifiant"
LS_ADMIN_PASSWORD="un-mot-de-passe-fort"
LS_SECRET_KEY="une-cle-longue-et-aleatoire"
```

Sur Windows PowerShell :

```powershell
$env:LS_ADMIN_USER="votre-identifiant"
$env:LS_ADMIN_PASSWORD="un-mot-de-passe-fort"
$env:LS_SECRET_KEY="une-cle-longue-et-aleatoire"
python app.py
```

## Rapports de test

- `LS-DIA-2026-0001`
- `LS-GEM-2026-0001`

## Mise en production

Pour un vrai déploiement public, ajouter : HTTPS, sauvegardes automatiques, comptes administrateurs avec mots de passe hachés, journal d'audit, protection CSRF, stockage privé des PDF, contrôle d'accès renforcé et hébergement adapté.

## Mention importante

Ce système est une base interne La Source. Il ne doit pas être présenté comme un service GIA, IGI ou HRD et n'implique aucune affiliation avec ces organismes.
