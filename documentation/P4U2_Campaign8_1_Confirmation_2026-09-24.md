# P4-U.2 — Campagne 8.1 : confirmation à deux étages (2026-09-24)

Exécute la confirmation C8.1 minimale demandée par le porteur du projet après le
diagnostic `2631252` : **A** calibration nulle (configuration actuelle + variation du
nombre de classes), **B** détection (configuration actuelle + variation de taille du
signal). Protocole et critères figés **avant** tout run dans `PREREGISTRATION.md`
(sha256 `d1c9abb1…483d44a`). **Aucune modification de
`p4u2_autonomous_relation_discovery_v0_1.py`. Aucune décision d'architecture.**

## 0. Réserve de reconstruction (à lire en premier)

Les scripts jetables C8/C8.1 n'ont jamais été committés. Le harnais
(`c81_confirmation.py`) est **reconstruit** depuis le module de production et les
rapports C8/C8.1. Il n'est pas le script d'origine :
- signatures : `compute_signatures` de production, avec un cache par source vérifié
  bit à bit identique sur 30 graphes (même appel `discover_paths(start=source)`) ;
- `T = max_s |G_s|` via `group_by_signature()` de production, percentile mid-rank de
  production, rejet si ≥ 95 ;
- générateur : arêtes `rng.sample(univers, 2)` ; null = même générateur, univers
  complet de nœuds, même nombre d'arêtes ;
- signal : c chaînes à 2 sauts sur 3c nœuds dédiés + 80 arêtes de fond sur 60 nœuds.
  Ce choix a été retenu parce qu'il reproduit C8.1 ; la variante « chaînes posées sur
  les nœuds de fond » donne T ∈ [3, 8], incompatible avec C8.1.

**Ancrage R0** (mêmes tailles que C8.1, graines neuves) :

| | C8.1 publié | R0 reconstruit |
|---|---|---|
| bruit, 40 graines, N_null=50 | FPR 2/40 | FPR 5/40 = 12,5 % [5,5 ; 26,1], binomial vs α_eff p = 0,055, PIT KS p = 0,72 |
| signal 15 chaînes, 25 graines | TPR 20/25, T ∈ [17, 27] | TPR 20/25, T ∈ [17, 24] |

L'ancrage est jugé satisfaisant (aucun test rejeté). Le 12,5 % se résorbe en A1
(4/100). La fidélité n'est pas démontrée au bit près : les conclusions portent sur le
mécanisme de production tel que reconstruit.

## 1. Point méthodologique préalable : ce que l'étage A peut et ne peut pas tester

En A1–A3, le graphe observé est tiré **par le générateur du null lui-même**. Observé et
réplicats sont donc échangeables, et la calibration y est garantie **par construction**,
quel que soit K. L'étage A ne teste que l'**implémentation** : c'est ce type de test qui
avait attrapé le bug du pool de C8, mais il n'établit pas que le null est approprié à un
corpus réel. C'est pourquoi un étage **A-bis** (graphe observé non uniforme, null
inchangé) a été pré-enregistré, en supplément et hors critère.

Second point : T est entier, avec beaucoup d'ex-aequo (masse d'égalité jusqu'à 23 %).
Le test mid-rank ≥ 95 n'a donc pas une taille exacte de 5 %. Sa taille réelle α_eff est
estimée par leave-one-out sur les réplicats nuls, et tous les tests binomiaux sont faits
contre α_eff. L'uniformité est testée sur un PIT randomisé, exactement U(0,1) sous
échangeabilité, plutôt que sur les percentiles bruts, qui ne peuvent pas être uniformes
avec des ex-aequo.

## 2. Étage A — calibration nulle (100 graines, N_null = 200)

| config | nœuds/arêtes | K obs / null | FPR | Wilson 95 % | α_eff | binom. bilat. | KS PIT | χ² PIT |
|---|---|---|---|---|---|---|---|---|
| A1 | 60/100 | 70,9 / 71,4 | 4/100 | [1,6 ; 9,8] | 4,00 % | 1,00 | 0,77 | 0,47 |
| A2 | 150/100 | 44,3 / 43,6 | 4/100 | [1,6 ; 9,8] | 4,98 % | 0,82 | 0,78 | 0,66 |
| A3 | 250/100 | 24,7 / 24,9 | 8/100 | [4,1 ; 15,0] | 5,06 % | 0,17 | 0,37 | 0,12 |

**N1, N2 : PASS pour les trois** (seuil Bonferroni 0,0167). K varie d'un facteur 2,9
à nombre d'arêtes fixé. Le régime de T change complètement (médiane 5 → 26,5 → 46),
sans perte de calibration. A3 est légèrement au-dessus du nominal (8 %), mais cela
reste compatible (p = 0,17). C'est à surveiller si une future configuration pousse
encore la parcimonie.

## 3. Étage A-bis — null mal spécifié (supplémentaire, hors critère)

60 nœuds / 100 arêtes, graphe observé à degrés hétérogènes (Zipf s=1), **aucun signal
injecté**, null uniforme inchangé :

```text
FPR = 88/100   Wilson [80,2 % ; 93,0 %]   médiane des percentiles = 100
```

**Deux causes distinctes, séparées par décomposition :**

1. **Artefact de troncature `MAX_PATHS=1000` (défaut du code de production).**
   Vérifié via `compute_signatures` de production sur 20 graphes : 101 sources
   dépassent 1000 chemins, 819/2000 arêtes (41 %) en dépendent, et 236 reçoivent la
   signature vide `(0,0,0,∅)`, toutes issues d'une source tronquée. Leur signature
   dépend alors de l'**ordre d'énumération**, pas de la structure.
   `group_by_signature()` les réunit en un bucket artificiel, qui porte T dans 60 %
   des graphes. Aucune troncature n'a lieu en A1–A3 ni en B.
2. **Mauvaise spécification du null lui-même.** Si ce bucket est exclu du maximum,
   côté observé comme côté null, le FPR reste à **58/100** [48,2 ; 67,2]. Une simple
   hétérogénéité de degrés, sans aucune classe relationnelle, suffit donc à rejeter
   H0.

Le null uniforme ne teste donc pas « existe-t-il une classe relationnelle ? ». Il
teste « ce graphe est-il un graphe aléatoire uniforme ? ». Sur un corpus réel, dont
les degrés ne sont presque jamais uniformes, le test rejetterait presque toujours.

## 4. Étage B — détection (100 graines, N_null = 200)

| config | chaînes | TPR | Wilson 95 % | binom. > α_eff | médiane pct | T obs (méd.) | T null (méd.) |
|---|---|---|---|---|---|---|---|
| B2 | 8 | 32/100 | [23,7 ; 41,7] | 3,8e-18 | 90,5 | 14 | 10 |
| B1 | 15 | 72/100 | [62,5 ; 79,9] | 1,5e-70 | 98,1 | 21 | 14 |
| B3 | 25 | 100/100 | [96,3 ; 100] | 6,3e-130 | 100 | 30 | 19 |

**S1, S2 : PASS pour les trois.** Le déplacement est monotone en taille de signal et
reproductible sur 300 graines. B1 (72 %) est compatible avec les 80 % de C8.1, dont
l'IC était [60,9 ; 91,1].

**S3 et attribution : réserve majeure.** Dans 100/100 graphes B1 et B2 (et pour
100 des 101 buckets arg-max de B3), T est porté par le bucket **d'impasses**
`(1,0,0,{F})`. Ce bucket contient les **secondes** arêtes des chaînes (B→C, C de
degré 1), plus environ 6 impasses de fond. La signature propre au motif chaîne,
`(1,1,0,{F,FF})` portée par les premières arêtes, ne porte le maximum qu'une seule
fois (B3, à égalité).

| config | membres moyens du bucket arg-max : 1res arêtes / 2es arêtes / fond |
|---|---|
| B2 | 0,0 / 8,0 / 5,7 |
| B1 | 0,0 / 15,0 / 5,9 |
| B3 | 0,25 / 24,75 / 5,7 |

Le critère S3 tel que pré-enregistré (arg-max ≥ 50 % d'arêtes de chaîne) est
formellement satisfait (72/72, 28/32, 100/100). Mais il était mal posé : il compte
aussi les arêtes terminales, et ce que le test détecte réellement est **un excès
d'arêtes en cul-de-sac**, pas la classe « chaîne à 2 sauts ». Le signal injecté en
produit mécaniquement, en posant des chaînes sur des nœuds dédiés de degré 1. C'est
cohérent avec A-bis : T réagit à des écarts de distribution de degrés.

## 5. Verdict au regard des critères pré-enregistrés

```text
N1/N2  calibration nulle, 3 niveaux de K        PASS
S1/S2  détection, 3 tailles de signal           PASS
S3     attribution (non bloquant)               formellement PASS, interprétation NÉGATIVE
A-bis  null mal spécifié (hors critère)         FPR 88 % (58 % hors artefact)
```

Au sens strict des critères figés, **C8.1-confirmation est PASS.** Cette confirmation
**ne suffit pas à justifier l'intégration** :
- La calibration établie est conditionnelle à ce que H0 soit exactement le
  générateur du null. Elle ne dit rien d'un corpus réel.
- La « puissance » mesurée est celle d'un détecteur d'écart à l'uniformité des
  degrés. Ce n'est pas celle d'un détecteur de classe relationnelle.
- Un défaut de production est trouvé : la troncature de `edge_signature` produit des
  signatures dépendantes de l'ordre et un bucket artificiel. C'est un prérequis
  bloquant pour tout corpus avec hubs, quelle que soit la statistique retenue.

## 6. État recommandé

```text
P4-U.2
────────────────────────────────────────────
Cohesion_B + group_by_signature        INVALIDÉ
Support T=max|G_s|                     CALIBRÉ SOUS H0 = générateur du null ;
                                        NON SPÉCIFIQUE (détecte les impasses / degrés)
Null procédural uniforme               APPROPRIÉ si H0 uniforme, INADAPTÉ sinon (A-bis)
Correction de sélection globale        CONFIRMÉE (K de 25 à 71)
Troncature MAX_PATHS dans signatures   DÉFAUT DE PRODUCTION TROUVÉ, non corrigé
C8.1 confirmation                      PASS (critères figés), avec réserves ci-dessus
V1–V4                                  GELÉS
Production / Architecture              INCHANGÉES / GELÉE
```

## 7. Questions ouvertes pour le porteur du projet (aucune tranchée ici)

1. **Null conditionnel aux degrés** (configuration model / permutation d'arêtes
   préservant les degrés entrants et sortants), à la place du null uniforme. C'est la
   correction naturelle d'A-bis. Il faudrait la tester avec les mêmes étages A, A-bis
   et B, et vérifier si B conserve de la puissance une fois les impasses « expliquées »
   par les degrés.
2. **Statistique restreinte** aux signatures non triviales (d2 > 0 ou d3 > 0), pour
   ne plus mesurer les impasses. Ce serait une nouvelle statistique, à pré-enregistrer.
3. **Troncature** : rendre `edge_signature` indépendante de l'ordre (budget par arête,
   ou marquage explicite `TRUNCATED` exclu du regroupement). C'est une modification de
   production, donc une décision explicite.

## Fichiers

`PREREGISTRATION.md` (+ `.sha256`), `c81_confirmation.py`, `analyze.py`,
`attribution.py`, `abis_decomp.py`, `raw_*.json` (données brutes par graine),
`summary_*.json`, `attribution.json`.
