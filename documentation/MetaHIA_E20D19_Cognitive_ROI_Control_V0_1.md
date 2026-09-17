# MetaHIA — E20-D.19 — Contrôle cognitif / ROI de l’exploration structurelle v0.1

## Objectif
Introduire un contrôle de sélection des chemins candidats fondé sur le coût structurel, la nouveauté, la redondance et le gain épistémique attendu, sans filtre sémantique.

## Forme
Pour un candidat de chemin `P` :

`ROI(P) = ExpectedGain(P) × StructuralNovelty(P) × (1 - Redundancy(P)) / StructuralCost(P)`

La décision est déterministe à partir de seuils explicites :

- `EXPLORE` si ROI >= seuil d’exploration
- `DEFER` si ROI >= seuil de report
- `STOP` sinon

## Principe de non-interprétation
Le contrôleur ne lit jamais la signification des opérateurs, des nœuds ou des extrémités. Un chemin vers un objet sémantiquement inattendu reste admissible si ses critères structuraux/épistémiques justifient son exploration.

## Provenance
Chaque score conserve la provenance du `PathRecord`. Le contrôleur ne réécrit pas le graphe. Il autorise seulement la sélection pour une réinjection ultérieure.

## Résultat expérimental
- 12/12 assertions ciblées PASS.
- 122/122 tests pytest du dépôt PASS.
- Compilation PASS.
- `kernel2.py` inchangé : même SHA-256 `987839172357c4b0e43e5d3d03dcda32825f4da817dbb02390a5bc4c3f9ea3d9`.

## Portée
Ce résultat est `PASS_MICROSTRUCTURAL`. Le gain attendu est encore fourni par la couche appelante et les seuils restent des paramètres explicites. La métacognition adaptative (apprentissage de la politique d’exploration à partir des résultats historiques) reste ouverte.

## Validation tierce
La validation indépendante doit masquer les valeurs de gain/novelty choisies par l’implémentation et vérifier notamment qu’un lien sémantiquement « bizarre » n’est jamais rejeté uniquement pour cette raison, que les duplications sont pénalisées, et que l’ordre des candidats est déterministe.
