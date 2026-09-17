# MetaHIA V10.0 — Documentation de déploiement (2026-09-17)

## Portée

Ce document couvre le déploiement de **MetaHIA-V10-Research** (lignée de recherche K3 :
kernel2.py, E20-D, M3, M4, M5) sur le serveur sandbox du LAN de développement. Il ne couvre
pas l'application de production `MetaHIA-Consolidated-Repo`, qui n'a pas été modifiée par
cette opération.

Voir [`MIGRATION_V10_UPDATE_2026-09-17.md`](MIGRATION_V10_UPDATE_2026-09-17.md) pour le
détail de la comparaison de code, des fichiers portés et des 4 bugs corrigés dans
`kernel2.py` avant ce déploiement.

## 1. Backup de l'ancienne version

L'ancienne version de cette lignée de recherche (`research/k3_spike_e13a2/` du dépôt
`MetaHIA-Consolidated-Repo`) a été archivée et copiée sur le serveur sandbox **avant**
toute autre opération, de façon strictement additive (aucun fichier existant sur le
serveur n'a été modifié ou supprimé).

- Archive : `k3_spike_e13a2_backup_20260917T161211Z.tar.gz` (211 491 octets)
- Emplacement serveur : `192.168.1.11:~/backups/metahia-k3-research/`
- Intégrité : SHA-256 identique des deux côtés —
  `88046949e4d0e4d8980cbb2fe54ba4e82b06bd432d86f5a91895f7f87d462857`
  (vérifié par calcul sur la machine locale ET sur le serveur après transfert, pas
  seulement supposé après le transfert)

## 2. Déploiement de la nouvelle version

Le contenu mis à jour de `MetaHIA-V10-Research` (post-correction des 4 bugs, post-ajout
des 15 fichiers de test hérités) a été transféré et extrait dans un répertoire **neuf**,
sans toucher à quoi que ce soit d'existant sur le serveur (notamment le
`~/MetaHIA-Consolidated-Repo` déjà présent, qui appartient à un chantier distinct et n'a
pas été touché).

- Emplacement serveur : `192.168.1.11:~/MetaHIA-V10-Research/`
- Méthode : `scp` d'une archive tar.gz + extraction, intégrité vérifiée par SHA-256 avant
  extraction (`6b33ce6be58bb4a2e8dd25a3828eae5e320d8a791f256b715841796cca4e3156`)
- Vérification post-déploiement : suite de tests complète exécutée **sur le serveur
  lui-même** (pas seulement rejouée localement), avec l'environnement Python déjà présent
  sur ce serveur (`~/metahia-sandbox/MetaHIA-Consolidated-Repo/.venv`, Python 3.10.12,
  pytest 9.1.1) :

  ```
  277 passed in 0.78s
  ```

  Résultat identique à l'exécution locale (Windows, Python 3.13.14) — aucune divergence
  d'environnement constatée.

## 3. Ce qui n'a PAS été fait

- Aucun service d'infrastructure du sandbox (Postgres/Neo4j/Qdrant/Redis/MinIO,
  `deploiement-sandbox/provision_sandbox.sh`) n'a été démarré, arrêté ou reconfiguré : ce
  déploiement concerne uniquement le code source de recherche K3, pas l'infrastructure de
  données du sandbox, qui est un chantier distinct.
- Le dépôt `~/MetaHIA-Consolidated-Repo` déjà présent sur le serveur n'a pas été modifié.
- Aucun identifiant, mot de passe ou jeton n'a été saisi ou stocké pendant cette
  opération : l'accès au serveur utilise l'authentification par clé SSH déjà configurée
  (`~/.ssh/config`, hôte `192.168.1.11`, utilisateur `bacem`), sans mot de passe.

## 4. Publication GitHub — étape restante, à compléter par l'utilisateur

Le dépôt Git local `MetaHIA-V10-Research` a été initialisé et commité, prêt à être
poussé vers un nouveau dépôt GitHub privé du même nom. **Cette étape n'a pas pu être
complétée automatiquement** : ni le CLI `gh` (installé mais non authentifié), ni git,
n'avaient d'identifiants GitHub configurés dans cette session, et créer un nouveau dépôt
ou s'authentifier nécessite une action humaine (connexion OAuth dans un navigateur) —
volontairement jamais automatisée avec des identifiants en clair.

Pour finaliser, exécutez l'une des deux options suivantes :

**Option A — via le CLI `gh` (recommandé)**
```powershell
& "C:\Program Files\GitHub CLI\gh.exe" auth login
# suivez l'invite (connexion navigateur), puis :
cd C:\tmp\metahia_v10_repo
& "C:\Program Files\GitHub CLI\gh.exe" repo create MetaHIA-V10-Research --private --source=. --remote=origin --push
```

**Option B — créer le dépôt manuellement sur github.com puis pousser**
```powershell
cd C:\tmp\metahia_v10_repo
git remote add origin https://github.com/<votre-compte>/MetaHIA-V10-Research.git
git push -u origin main
```

Une fois poussé, redites-le-moi si vous voulez que je vérifie l'état du dépôt distant ou
que j'y apporte d'autres modifications.
