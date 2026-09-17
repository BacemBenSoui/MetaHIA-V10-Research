# MetaHIA — Protocole de validation tierce E20-D.19 v0.1

## But
Vérifier indépendamment que le contrôle ROI arbitre l’exploration sur des critères structurels/épistémiques et non sur le sens des labels.

## Matériel
Utiliser `kernel2.py` et `e20d_cognitive_control_v0_1.py` fournis dans le paquet, sans modification.

## Cas obligatoires
1. Chemin court / gain élevé : doit être `EXPLORE`.
2. Chemin plus coûteux à gain intermédiaire : doit être `DEFER`.
3. Chemin faible gain : doit être `STOP`.
4. Même chemin déjà mémorisé : pénalité de redondance.
5. Deux références différentes avec payload/labels semblables : ne jamais fusionner l’identité.
6. Endpoint arbitraire (ex. `Moto`) : ne jamais refuser pour une raison sémantique.
7. Deux candidats à ROI identique : ordre déterministe par identifiant.
8. Provenance conservée inchangée dans le score.
9. Seuils inversés : refus explicite.
10. Gain négatif : clamp à zéro / aucune exploration forcée.

## Critère de réussite
Aucun échec ne doit provenir d’une interprétation sémantique des labels. Toute décision doit être expliquée par `ROI`, `cost`, `novelty`, `redundancy` et les seuils explicites.

## Limites à vérifier séparément
Le tiers doit confirmer que la présente brique n’est pas encore une métacognition apprenante : elle applique une politique paramétrée, elle ne l’apprend pas.
