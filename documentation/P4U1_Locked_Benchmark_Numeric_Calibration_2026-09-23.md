# P4-U.1 — Calibration numérique du benchmark verrouillé U1/U2/U3 (2026-09-23)

Ce document enregistre, avant toute comparaison contre un résultat de holdout
verrouillé, comment les valeurs numériques manquantes de la checklist de
`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_3.md`
Sec. 16 (points 2/7/8/11) ont été fixées — exigence explicite du protocole
lui-même : « choisies dans le protocole avant le benchmark verrouillé...
jamais après avoir vu un résultat de holdout ».

Toute la calibration ci-dessous a été effectuée sur des corpus **jetables**,
générés par des scripts Python exécutés directement en ligne de commande,
**jamais committés** — seule cette page et les valeurs finales retenues dans
`p4u1_locked_benchmark_cases_v0_1.py` (`GATE_PARAMS`) constituent l'enregistrement
permanent de cette étape.

## 1. Premier constat, corrigé avant toute calibration utile

Une première tentative de structure « hub » (plusieurs branches partant d'un
même nœud, chaque branche de degré 1) s'est révélée être exactement la
structure « plate » dont la Sec. 20 du protocole v0.2 avait déjà prouvé
l'invariance algébrique face au modèle nul à degré exact préservé — et,
empiriquement, le modèle nul par pool (actuellement verrouillé) produisait
même un maximum **supérieur** au signal réel dans cette configuration (ex. :
k=3 hubs × m=5 branches → support réel 15, mais percentile 99 du maximum nul
≈ 27-36), un résultat contre-intuitif mais reproductible : avec des tirages
uniformes sur un pool de taille comparable au nombre de tirages, le
maximum d'un processus « boules dans des bacs » peut dépasser une
concentration délibérée mais faible.

**Corrigé** : la concentration qui compte pour Gate B est le produit
`in_degree_A(pont) × out_degree_B(pont)` **sur un seul nœud-pont**, pas le
nombre de branches partageant une origine commune. Une structure
« pont unique » (P parents convergeant vers UN pont, Q enfants en
divergeant, support = P×Q) donne une séparation réelle et large dès une
échelle modeste :

| P | Q | distracteurs (chaque REL_A/REL_B) | support réel | null p99 | null max |
|---|---|---|---|---|---|
| 8 | 8 | 60 / 60 | 64 | 6-9 | 8-12 |
| 20 | 20 | 30 / 30 | 400 (discovery) / 20 (holdout, existence) | 12 | 16 |
| 25 | 15 | 30 / 30 (holdout) | 375 (discovery) / 25 (holdout, existence) | 10 | 16 |

## 2. Distinction importante : statistique de découverte (TRAIN) vs statistique d'existence (HOLDOUT)

Le support côté TRAIN (Gate B) reste le compte total de chemins
(`P × Q`, une statistique de *découverte*). Le `support_holdout` côté Gate C
(Sec. 10.2 de la v0.3) est un compte de **starts qui répliquent**, une
statistique d'*existence* — pour la structure « pont unique », cela vaut
exactement `P` (chaque parent est un start distinct, indépendamment du
nombre d'enfants qu'il atteint). Ces deux statistiques ne sont pas sur la
même échelle et ne doivent jamais être confondues lors du choix des seuils
(`S_min` compare au support de découverte ; `K_min` compare au compte de
starts répliquants).

## 3. `max_paths` — passé de `None` à une limite fixe après mesure directe

`max_paths=None` (recommandation par défaut de la Sec. 13 pour un petit
graphe) a été essayé en premier et s'est révélé, par exécution directe,
prohibitivement lent (jusqu'à ~60 s pour un seul calcul de distribution du
maximum nul à 200 réplicats, dès qu'un réplicat concentre par hasard assez
de degré sur un nœud pour faire exploser combinatoirement l'énumération de
chemins de profondeur 3). Remplacé par la limite fixe que la Sec. 13
prévoit elle-même comme repli (« sinon : une limite fixe, IDENTIQUE sur
G_train ET tous les G_negative... et sur G_holdout et tous les
G_holdout_negative ») : **`max_paths = 1000`**, appliquée uniformément à
tous les appels de ce benchmark (train, holdout, et tous leurs réplicats
nuls). Vérifié : cette limite ne tronque aucun signal réel (le plus grand
compte de chemins réel du benchmark, 375, reste très en dessous, et aucun
candidat retenu ne change de verdict entre `max_paths=None` et
`max_paths=1000`).

## 4. Valeurs numériques finales retenues (`GATE_PARAMS`)

```text
min_depth        = 2      (Sec. 5, déjà fixé)
max_depth        = 3      (Sec. 5, déjà fixé)
max_paths        = 1000   (Sec. 13 -- voir point 3 ci-dessus)
n_null           = 200    (Sec. 6, défaut déjà annoncé, confirmé ici)
null_percentile  = 99.0   (Sec. 7/9/10, déjà le défaut du code)
s_min            = 15     (Gate B -- voir point 5)
k_min            = 15     (Gate C -- voir point 5)
coverage_min     = 0.10   (Gate C -- voir point 5)
```

## 5. Justification de S_min / K_min / coverage_min sur les corpus finaux (calibration jetable)

Mesures directes sur les corpus finalement retenus (mêmes structures que
`p4u1_locked_benchmark_cases_v0_1.py`, avec `max_paths=1000`) :

```text
U1 TRAIN  : REAL_MOTIF support=64, DECOY_TRAIN_ONLY support=64,
            DECOY_SUB_SEUIL support=4, null p99=6
U1 HOLDOUT: REAL_MOTIF support_holdout=25 (coverage=0.171),
            DECOY_TRAIN_ONLY support_holdout=0 (coverage=0.0),
            null p99=10
U2 TRAIN  : REAL_MOTIF support=64, null p99=6
U2 HOLDOUT: REAL_MOTIF support_holdout=0, null p99=0
U3 TRAIN  : 2 candidats (forward+reverse), support=37 chacun, null p99=50-54
            (robuste sur 10 seeds testés, seed=0 retenu -- voir Sec. 6)
```

`S_min = 15` : strictement entre `DECOY_SUB_SEUIL` (4) et les deux
candidats concentrés (64), et au-dessus du null p99 côté train (6-9 selon
le cas) — marge large des deux côtés, jamais un seuil « à la limite ».

`K_min = 15` : strictement entre `DECOY_TRAIN_ONLY`/`U2` (0) et
`REAL_MOTIF` (25), et au-dessus du null p99 côté holdout (10) — même
discipline de marge.

`coverage_min = 0.10` : en dessous de la couverture réelle mesurée pour
`REAL_MOTIF` (0.171, soit ~17 %) mais loin au-dessus de 0 (le cas
d'échec) — un seuil non trivial mais pas ajusté au plus près du résultat
observé.

## 6. U3 — choix du seed du modèle nul, vérifié robuste sur 10 tirages

`G_train` de U3 est produit par `null_generator()` appliqué à une base
« plate » à 40 ponts de degré 1 (Sec. 14 : « généré par la même procédure
que null_generator(), traité comme le vrai G_train de ce cas »). Le seed
`0` a été retenu après vérification, par exécution directe, que
`any_retained == False` (aucun candidat ne dépasse son propre percentile
99 du maximum nul) tient sur **10 seeds consécutifs testés (0 à 9)**, pas
seulement le seed finalement choisi — un contrôle de robustesse du CAS
lui-même (« est-ce une base représentative d'une absence de régularité »),
pas un réglage des seuils de Gate B/C pour faire réussir un résultat
particulier.

## 7. Ce que cette calibration ne fait PAS

Elle ne fixe aucune valeur en ayant vu le résultat du run RÉEL sur
`p4u1_locked_benchmark_cases_v0_1.py`/`_witness_v0_1.py` — toutes les
mesures ci-dessus proviennent de corpus jetables aux mêmes paramètres
structurels, jamais du fichier de cas verrouillé lui-même exécuté contre
son propre témoin. Le run verrouillé réel (`p4u1_locked_benchmark_runner_v0_1.py`)
a été exécuté seulement APRÈS que cette page et `GATE_PARAMS` aient été
figés.
