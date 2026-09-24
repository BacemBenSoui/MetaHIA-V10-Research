# P4-U.2 — Calibration jetable, campagne 7 (Volet C) : validation du modèle nul de Gate H contre un corpus structurel réel (2026-09-24)

Exécute le Volet C, pré-enregistré exactement comme spécifié par le
porteur du projet avant toute exécution, comme dernier test avant un
gel provisoire de Gate H :

```text
n_null (par cellule)  = 500
tailles de groupe      = 20, 30, 40
k cibles                = 5, 6, 7, 8, 9, 10, 12
seuil                   = percentile >= 95 %
statistique             = cohésion du dissident (Cohesion_B, inchangée)
correction              = même règle R1 + même modèle nul corrigé que
                          les campagnes 5/6, SANS AUCUNE MODIFICATION
```

**La question posée n'est PAS « quel k_min choisir ? »** — c'est :
« pour chaque configuration `(taille, k)`, quel est le comportement réel
du test sous le null, quand le pool de fond provient de données
structurelles RÉELLES plutôt que d'un pool synthétique conçu par
nous ? »

## 1. Pool de fond réel — jamais choisi ni ajusté pour arranger un résultat

Union brute de tous les `discovery_facts` et `evidence_facts` de quatre
corpus de faits déjà utilisés à travers les expériences M6/M7 de ce
dépôt (`corpus/organization_facts_v0_1.json`,
`supply_chain_facts_v0_1.json`, `library_facts_v0_1.json`,
`family_tree_facts_v0_2.json`) — **134 faits au total, aucun filtrage,
aucune curation au-delà de la conversion de chaque ligne en observation
binaire K3.** Entités namespacées par domaine pour préserver la vraie
topologie de chaque domaine sans fusion accidentelle par réutilisation
de nom.

**Composition réelle obtenue (jamais construite pour ressembler à quoi
que ce soit) :**
```text
(has_depth2=1, has_depth3=1) : 97 arêtes (72 %)  -- chaînes profondes
(has_depth2=0, has_depth3=0) : 20 arêtes (15 %)  -- impasses
(has_depth2=1, has_depth3=0) : 17 arêtes (13 %)  -- un seul saut
```

Très différente des trois pools synthétiques de la campagne 6 (répartis
plus uniformément) — dominée aux deux tiers par des chaînes profondes,
typique de données réelles de généalogie/organisation/chaîne
d'approvisionnement où la continuation est la norme, pas l'exception.

## 2. Résultats — table complète, 21 cellules, 30 graines/cellule

| Taille | k | Utilisable | Taux de FP (≥95 %) | Hétérogénéité | Statut |
|---|---|---|---|---|---|
| 20 | 5 | 26/30 | 7,7 % | 97,2 | calibré |
| 20 | 6 | 28/30 | 7,1 % | 97,2 | calibré |
| 20 | 7 | 30/30 | 6,7 % | 97,2 | calibré |
| 20 | 8 | 30/30 | 3,3 % | 97,2 | calibré |
| 20 | 9 | 30/30 | 6,7 % | 97,2 | calibré |
| 20 | 10 | 30/30 | 0,0 % | 97,2 | calibré |
| 20 | 12 | 30/30 | 0,0 % | 97,2 | calibré |
| 30 | 5 | 27/30 | **18,5 %** | 99,6 | à surveiller |
| 30 | 6 | 29/30 | **13,8 %** | 99,6 | à surveiller |
| 30 | 7 | 29/30 | **20,7 %** | 99,6 | à surveiller |
| 30 | 8 | 29/30 | 3,4 % | 99,6 | calibré |
| 30 | 9 | 29/30 | 3,4 % | 99,6 | calibré |
| 30 | 10 | 30/30 | 0,0 % | 99,6 | calibré |
| 30 | 12 | 30/30 | 0,0 % | 99,6 | calibré |
| 40 | 5 | 29/30 | **20,7 %** | 100,0 | à surveiller |
| 40 | 6 | 28/30 | **14,3 %** | 100,0 | à surveiller |
| 40 | 7 | 28/30 | **14,3 %** | 100,0 | à surveiller |
| 40 | 8 | 30/30 | 3,3 % | 100,0 | calibré |
| 40 | 9 | 30/30 | 3,3 % | 100,0 | calibré |
| 40 | 10 | 30/30 | 3,3 % | 100,0 | calibré |
| 40 | 12 | 30/30 | 3,3 % | 100,0 | calibré |

(Seuil de statut purement descriptif ici : « calibré » si le taux de FP
≤ 10 %, « à surveiller » au-delà — une convention de présentation, pas
une décision de gel.)

## 3. Résultat central — le plancher trouvé sur pools synthétiques
   SURVIT sur un corpus réel, avec la même dépendance à la taille

**Sur les trois tailles, une transition nette apparaît entre k=7 (taux
de FP 6,7-20,7 %) et k=8 (taux de FP chute à 3,3-3,4 % partout) — la
même frontière qu'en campagne 6, maintenant confirmée contre un pool de
fond réel, non synthétique, de composition très différente (72 % de
chaînes profondes contre une répartition plus équilibrée).**

**La dépendance à la taille du groupe, trouvée en campagne 6, se
confirme aussi ici** : à k=5,6,7, la taille 20 donne des taux de FP
nettement plus bas (6,7-7,7 %) que les tailles 30 et 40 (13,8-20,7 %) —
exactement la même direction que la campagne 6 (où size=20/k=7 donnait
4,0 % contre size=40/k=7 donnant 13,8 %). **Ce n'est donc pas un
artefact du pool synthétique de la campagne 6 : la même relation
`(k, taille) → comportement du null` réapparaît sur des données réelles
totalement indépendantes.**

L'hétérogénéité manifeste reste toujours nettement séparée (97,2 à
100,0 selon la taille, jamais en dessous), confirmant une fois de plus
qu'aucune configuration testée ne fait passer inaperçue une vraie
seconde classe structurelle.

## 4. Réserve méthodologique explicite, comme demandé

**30 graines ne suffisent pas à distinguer un taux réellement nul d'un
taux simplement non observé dans cet échantillon.** Les `0,0 %` rapportés
à k=10/12 (toutes tailles) signifient « aucun faux positif observé sur
30 essais », pas « le taux réel est nul ». De même, les valeurs de
13,8-20,7 % à k=5-7 sont des signaux à prendre au sérieux, pas encore
des taux calibrés avec précision — un échantillon plus large serait
nécessaire pour les caractériser finement, mais **la cohérence de
direction et d'ordre de grandeur avec la campagne 6 (pools synthétiques)
rend ce signal crédible, pas un artefact d'échantillonnage isolé.**

Autre réserve : le pool réel (134 arêtes) est modeste comparé aux pools
synthétiques de 270 arêtes des campagnes 5-6 — tirer des groupes de 40
depuis un pool de 134 implique un recouvrement non négligeable entre
réplicats nuls successifs, une limite inhérente à la taille des données
réelles actuellement disponibles dans ce dépôt, pas un choix de
conception.

## 5. Conclusion pour la gouvernance de Gate H

**L'enveloppe de calibration `k ≥ 8` (tailles de groupe 20 à 40) est
maintenant validée sur QUATRE pools de fond indépendants** : les trois
compositions synthétiques pré-enregistrées de la campagne 6 (150/80/40,
120/90/60, 90/90/90) et ce pool réel dérivé de quatre corpus de faits
authentiques du dépôt. Dans les quatre cas, `k ≥ 8` donne un taux de
faux positifs proche du niveau nominal (0,0-6,7 %), tandis que `k ≤ 7`
montre un risque significativement élevé dans au moins une configuration
de taille.

Conformément au principe posé par le porteur du projet — ne jamais
répondre « k=7 est mauvais » mais « telle configuration n'est pas
encore dans l'enveloppe calibrée » — cette campagne fournit la table
empirique complète permettant cette formulation, sans imposer un seuil
« magique ». La décision de geler Gate H sous une forme *fail-closed*
(percentile ≥ 95 %, correction multi-comparaisons, évaluation limitée à
l'enveloppe `k ≥ 8` validée ici, `CALIBRATION_INSUFFICIENT` — jamais un
verdict de découverte — hors de cette enveloppe) revient maintenant au
porteur du projet, avec les preuves nécessaires réunies.
