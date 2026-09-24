# P4-U.2 — Calibration jetable, campagne 6 : trou petit-k (Volet A) et robustesse au pool (Volet B) (2026-09-24)

Exécute les volets A et B de la campagne demandée par le porteur du
projet après l'archivage de la campagne 5 (`56803a8`, confirmée baseline
de référence) comme trajectoire stricte vers le gel de Gate H. Le volet
C (pool dérivé d'un corpus réel) n'est **pas** tenté ici, conformément à
sa priorité plus basse (🟠) dans le plan du porteur du projet — signalé
comme prochaine étape, pas fait dans cette passe.

```text
56803a8 (campagne 5, archivée comme baseline)
        ↓
campagne 6
   Volet A : k ∈ {3,4,5,6,7}, 200 graines/cellule  <- CE DOCUMENT
   Volet B : robustesse à 3 compositions de pool   <- CE DOCUMENT
   Volet C : pool dérivé d'un corpus réel          <- PAS FAIT (🟠)
        ↓
gel numérique de Gate H (toujours pas fait)
```

## Volet A — le trou laissé par la campagne 5 (k=3 à 7), 200 graines

Même modèle nul corrigé et même pool que la campagne 5 (270 arêtes,
80/150/40), même règle R1. Groupe candidat de taille fixe 20 dans toute
cette section (les cinq niveaux de `k` sont obtenus en faisant varier
uniquement la fraction de contamination, pas la taille du groupe — voir
réserve en Sec. 4).

| k cible | Fraction | Utilisable | k moyen réel | percentile moyen | P95 empirique | max percentile | Taux de FP (≥95 %) | Taux de FP (≥99 %) | Hétérogénéité |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 0,15 | 152/200 | 3,3 | 31,2 | 97,8 | 98,0 | **25,0 %** | 0,0 % | 97,5 |
| 4 | 0,20 | 173/200 | 3,9 | 31,6 | 98,2 | 98,2 | **19,7 %** | 0,0 % | 97,5 |
| 5 | 0,25 | 188/200 | 4,8 | 21,0 | 97,2 | 97,8 | 8,0 % | 0,0 % | 97,5 |
| 6 | 0,30 | 196/200 | 5,3 | 27,0 | 98,2 | 99,0 | 7,1 % | 2,6 % | 97,5 |
| 7 | 0,35 | 200/200 | 6,3 | 25,7 | 85,5 | 99,0 | 4,0 % | 3,0 % | 97,5 |

**Résultat net, avec 200 graines (contre 20 en campagne 5) : le taux de
faux positifs DÉCROÎT DE FAÇON MONOTONE et clairement mesurable de k=3
(25,0 %) à k=7 (4,0 %, essentiellement au niveau nominal).** Ceci révèle,
avec une résolution que 20 graines ne permettaient pas, une vraie
dégradation du null corrigé aux très petits effectifs — non éliminée par
la correction de la campagne 5, seulement non visible dans la plage
qu'elle avait testée (k≥7).

## Volet B — robustesse à 3 compositions de pool pré-enregistrées

Trois pools, pré-enregistrés avant exécution, jamais choisis après avoir
vu quel résultat « arrangerait » la conclusion : `P1 = 150/80/40`
(baseline, identique à la campagne 5), `P2 = 120/90/60`, `P3 = 90/90/90`.
30 graines par cellule, k ∈ {7,8,9,10,12,15} (mêmes tailles de groupe que
la campagne 5 : 40 pour k≤10, 60 pour k=12/15).

| k cible | P1 (150/80/40) | P2 (120/90/60) | P3 (90/90/90) | Hétérogénéité (les 3 pools) |
|---|---|---|---|---|
| 7 | FP=13,8 % | FP=13,8 % | FP=13,8 % | 100,0 |
| 8 | FP=3,3 % | FP=0,0 % | FP=0,0 % | 100,0 |
| 9 | FP=0,0 % | FP=0,0 % | FP=0,0 % | 100,0 |
| 10 | FP=6,7 % | FP=3,3 % | FP=6,7 % | 100,0 |
| 12 | FP=0,0 % | FP=0,0 % | FP=0,0 % | 100,0 |
| 15 | FP=0,0 % | FP=0,0 % | FP=0,0 % | 100,0 |

**Le comportement qualitatif est remarquablement stable sur les trois
pools** — mêmes ordres de grandeur à chaque niveau de `k`, aucune
composition ne se démarque systématiquement des deux autres. **Ce n'est
donc pas la composition 150/80/40 qui fabrique artificiellement le bon
comportement** : la propriété survit à des populations de fond
sensiblement différentes. L'hétérogénéité manifeste reste séparée de
façon parfaite (percentile 100,0 exactement) sur les 18 cellules
(3 pools × 6 niveaux de k), sans exception.

## Résultat combiné — ce que les deux volets établissent ensemble

```text
k=3-4   : taux de FP nettement élevé (19,7-25,0 %) -- non sûr
k=5-6   : taux de FP intermédiaire (7,1-8,0 %) -- encore au-dessus du
          niveau nominal, marge insuffisante
k=7     : ZONE FRONTIÈRE -- 4,0 % à taille 20 (Volet A), mais 13,8 %
          à taille 40, stable sur 3 pools (Volet B) -- le résultat
          dépend de la taille du groupe, pas seulement de k
k=8-9   : proche ou au niveau nominal (0,0-3,3 %), stable sur 3 pools
k≥10    : systématiquement bas (0,0-6,7 %), stable sur 3 pools
```

**Constat important, distinct de celui de la campagne 4** : un plancher
réel existe bien aux petits effectifs, mais il n'est pas une fonction de
`k` seul — la cellule `k=7` se comporte différemment selon que le groupe
candidat fait 20 ou 40 observations, à contamination ajustée pour
atteindre le même `k` moyen. Ceci confirme le point conceptuel soulevé
par le porteur du projet (Sec. 7 de sa proposition) : **la bonne
abstraction n'est pas un simple seuil `k < X → invalide`, mais la
statistique de cohésion comparée à SA distribution nulle propre — un
plancher approximatif reste néanmoins pratiquement nécessaire pour
éviter d'évaluer Gate H sur des effectifs où le null lui-même reste
insuffisamment résolu.**

## Ce que cette campagne établit, et ce qu'elle n'établit pas

**Établi, par exécution directe** :
- Avec une résolution de 200 graines, une vraie dégradation monotone du
  taux de faux positifs existe entre k=3 et k=7 sous le null corrigé de
  la campagne 5 — ce n'était pas visible avec 20 graines.
- Ce comportement qualitatif (dégradation aux petits k, stabilisation
  autour de k≈8-10) est stable sur trois compositions de pool
  sensiblement différentes, pré-enregistrées avant exécution.
- L'hétérogénéité manifeste reste séparée de façon parfaite (100,0) à
  chaque niveau de k testé (7 à 15) et sur chaque pool testé, sans
  exception — reconfirmé, pas seulement supposé.

**Non établi, délibérément** :
- Une valeur unique de `k_min` — le comportement à k=7 dépend de la
  taille du groupe, pas seulement de k, donc un plancher exprimé en
  effectif absolu seul est une approximation, pas une loi exacte.
- Le comportement à des tailles de groupe intermédiaires entre 20 et 40
  (non testées ici).
- Un taux de faux positifs précisément calibré à k=8-10 (les cellules à
  0,0 % avec 30 graines ne garantissent pas un vrai taux nul — seulement
  un taux compatible avec le niveau nominal à cette résolution).
- Le Volet C (pool dérivé d'un corpus réel) — non tenté, reste la
  prochaine étape recommandée par le porteur du projet lui-même, à
  priorité plus basse que les Volets A/B.

## Prochaine étape

Conformément à la trajectoire proposée par le porteur du projet
(campagne 6 → gel de Gate H → retour à P4-U.1), les résultats des Volets
A et B sont maintenant disponibles pour informer une décision de gel
provisoire (`HYPOTHESIS_ONLY` en attendant, comme proposé). Le Volet C
reste ouvert comme prolongement possible mais non bloquant. La décision
de geler Gate H (plancher approximatif + seuil percentile ≥95 %) ou de
prolonger encore la calibration revient explicitement au porteur du
projet.
