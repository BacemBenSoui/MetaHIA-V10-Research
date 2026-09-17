# MetaHIA — Matrice de validation consolidée v0.1

| Objet | Théorique / conceptuel | Test atomique/local | Tierce | Empirique / holdout | Statut |
|---|---|---|---|---|---|
| K3 / R-V-1 | Oui | Oui | Oui sur périmètres audités | Partiel | FROZEN baseline |
| M1 | Oui | suite ciblée + régression | via paquets de validation des sous-capacités | ouvert | STABLE |
| M2 | Oui | ciblé | pas encore gate générale | corpus historique insuffisant pour claim général | NON-PROMOTED |
| E20-D D1–D19 | Oui | microstructurel | partiel / selon sous-gate | autonomie générale ouverte | OPEN |
| M3 | Oui | 10/10 + 8/8 + 140/140 | 18/18 | périmètre critique seulement | PASS_INDEPENDENT_SCOPE |
| M4 | Oui | 25/25 + 131/131 | positive selon décision projet | mesure réelle N_min encore à élargir | PASS_INDEPENDENT_SCOPE |
| M5 | Oui | 26/26 + 157/157 | 26/26 ×3, 10/10 exigences | benchmark critique, pas généralisation | PASS_INDEPENDENT_SCOPE |
| M6 | Oui | à implémenter | à planifier | holdout obligatoire | GATED FOR IMPLEMENTATION |
| Parseur | spécifié | non implémenté | non | non | DEFERRED |
| LLM live | spécifié | non implémenté | non | non | DEFERRED |

## Règle
Aucune démonstration locale ne vaut validation scientifique générale. Tout claim supérieur doit citer son périmètre et son type de vérification.
