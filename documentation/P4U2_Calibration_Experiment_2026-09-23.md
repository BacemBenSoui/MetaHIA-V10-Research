# P4-U.2 — Calibration jetable : statistique de cohésion × modèle nul × Gate H (2026-09-23)

Ce document exécute l'étape explicitement demandée par le porteur du
projet après la lecture du protocole `documentation/P4U2_Protocol_V0_1.md` :
une **calibration jetable**, sur des corpus synthétiques disposables, des
trois verrous scientifiques identifiés comme prioritaires par rapport à
l'implémentation :

```text
P4U2_Protocol_V0_1.md (commit f6a96b2, gelé)
        ↓
calibration jetable                <- CE DOCUMENT
   - statistique de cohésion (A/B/C, testées, pas choisies a priori)
   - modèle nul (topologie vs assignation de groupe, testés séparément
     puis combinés)
   - Gate H (tolérance de contradiction, pilote quantitatif)
        ↓
gel numérique (pas fait ici)
        ↓
implémentation minimale (pas commencée)
```

**Aucun code de production P4-U.2 n'est créé ici. Aucune valeur numérique
n'est gelée. Aucun benchmark verrouillé V1-V4 n'est construit** — le
protocole (Sec. 14/16) l'interdit explicitement avant cette calibration,
et cette calibration elle-même produit un tableau d'aide à la décision,
pas une décision. Le script d'exécution est **jetable, non committé**
(même discipline que `scripts/_scratch_p4u1_calibration.py` pour P4-U.1),
exécuté depuis le scratchpad de session ; seuls les résultats et leur
analyse sont conservés ici.

## 1. Méthode

Pour chaque corpus synthétique, chaque observation reçoit un opérateur
masqué **individuel** (`OP#00000`, `OP#00001`, ...), méthode gelée en
Sec. 5 du protocole. La signature structurelle par arête est **exactement**
celle testée par l'expérience d'identifiabilité du 2026-09-23
(`P4U2_Identifiability_Experiment_2026-09-23.md`, Sec. 1), inchangée :

```text
Signature(arête) = ( nb chemins profondeur 1 dont le 1er pas est cette arête,
                      nb chemins profondeur 2 idem,
                      nb chemins profondeur 3 idem,
                      ensemble des séquences de direction observées )
```

calculée via `kernel2.discover_paths()` non modifié, `max_depth=3`,
`max_paths=1000`.

### 1.1 Trois statistiques de cohésion candidates (Sec. 8 du protocole)

- **Cohesion_A** (proportion de traits structuraux communs) : binarise
  chaque signature sur deux traits (`a un prolongement profondeur 2`,
  `a un prolongement profondeur 3`), moyenne la fraction d'accord
  majoritaire par trait sur le groupe.
- **Cohesion_B** (distance intra-groupe moyenne, convertie en cohésion via
  `1 / (1 + distance_moyenne)`) : distance = écarts absolus sur
  `depth2_count`/`depth3_count` + `1 - Jaccard` sur les ensembles de
  séquences de direction, moyennée sur toutes les paires du groupe.
- **Cohesion_C** (score de concentration multi-profondeur) : fréquence de
  la classe de signature complète la plus fréquente dans le groupe,
  divisée par la taille du groupe. **Choisie délibérément parce que
  c'est la même logique que la vérification par égalité exacte de
  signature que l'expérience d'identifiabilité a prouvée insuffisante
  EN ISOLATION** — testée ici volontairement avec une comparaison à un
  modèle nul, pour vérifier si l'ajout d'un modèle nul la rend viable
  plutôt que de l'écarter par principe.

### 1.2 Trois variantes de modèle nul (Sec. 9 du protocole, question
    explicitement laissée ouverte)

- **topology-only** : casse la topologie de TOUT le graphe (réassignation
  aléatoire globale source/target de chaque arête ; sans stratification
  par label, contrairement au modèle nul de P4-U.1, puisque le masquage
  individuel ne fournit aucun label partagé sur lequel stratifier —
  choix de conception explicite, pas une réutilisation silencieuse).
  Recalcule ensuite la cohésion du MÊME groupe candidat (mêmes indices
  d'arête) sur la nouvelle topologie.
- **group-resample-only** : garde la topologie réellement observée
  intacte, tire un sous-ensemble aléatoire de même taille que le groupe
  candidat parmi TOUTES les arêtes du corpus, recalcule la cohésion sur
  ce sous-ensemble (signatures mises en cache, calculées une seule fois
  sur le graphe réel).
- **combined** : les deux à la fois (topologie cassée + sous-ensemble
  aléatoire de même taille).

`N_null = 200` pour chaque variante et chaque statistique. Percentile en
convention **mid-rank** : `(nb_strictement_inférieur + 0.5 * nb_égal) /
N_null` — voir Sec. 2.2 ci-dessous pour pourquoi (bug trouvé et corrigé).

### 1.3 Quatre corpus synthétiques, jetables

- **SEP** (signal net) : 20 arêtes réelles avec prolongement profondeur 2
  garanti, plus 20 arêtes de prolongement (jamais elles-mêmes prolongées)
  et 20 arêtes-leurres en impasse. Groupe candidat = les 20 arêtes
  réelles.
- **TWIN** (population réellement homogène) : 4 cycles orientés disjoints
  de longueur 20 (80 arêtes). Par construction, **chaque arête a une
  signature strictement identique** — aucun sous-ensemble ne devrait être
  distinguable d'un autre. Groupe candidat = un cycle complet (20 arêtes).
- **PARTIAL** (reproduction exacte du Corpus 3 de l'expérience
  d'identifiabilité) : groupe candidat de 20 arêtes (16/20 = 80 % avec
  prolongement, 4/20 = 20 % sans), fond de 20 arêtes avec la répartition
  inversée (20 %/80 %) — le cas difficile qui avait fait échouer la
  vérification naïve par égalité.
- **PURE_NULL** (5 répétitions indépendantes) : graphe purement aléatoire,
  aucune structure intentionnelle, groupe candidat = sous-ensemble
  aléatoire — jauge grossière de taux de faux positifs.

## 2. Deux erreurs de méthode trouvées et corrigées avant toute conclusion

### 2.1 Construction initiale de TWIN invalide

Une première version de TWIN utilisait 40 arêtes « primaires » (toutes
avec prolongement) plus 40 arêtes de prolongement elles-mêmes en impasse
(prolongement = 0), avec le groupe candidat = les 40 arêtes primaires.
Le modèle `group-resample-only` tire alors son échantillon nul dans les
**80** arêtes (primaires + impasses mélangées) — un pool structurellement
hétérogène par construction. Le groupe candidat (100 % primaire)
apparaissait alors « significatif » non pas parce qu'il est
spécifiquement cohérent, mais simplement parce qu'il ne contient aucune
arête du second rôle structurel (impasse) — ce n'était pas un cas nul du
tout, c'est un doublon déguisé du signal déjà testé par SEP. **Trouvé et
corrigé avant de lancer la calibration complète** : TWIN reconstruit en 4
cycles orientés disjoints où LITTÉRALEMENT chaque arête a une signature
identique, rendant tout sous-groupe structurellement interchangeable
avec tout autre.

### 2.2 Percentile « <= » saturant à 100 % sur un cas nul dégénéré

La première définition du percentile (`fraction des valeurs nulles <=
valeur observée`) donne **100 %** dès que la distribution nulle est
entièrement égale à la valeur observée (cas parfaitement homogène) — un
résultat trompeur : TWIN/group-resample donnait percentile = 100 % alors
que le z-score valait exactement 0 (aucune séparation réelle). Corrigé
par une convention **mid-rank** standard
(`(nb_inférieur + 0.5*nb_égal)/N`), qui place correctement ce cas à 50 %.
Tous les résultats rapportés ci-dessous utilisent la version corrigée.

## 3. Résultats

### 3.1 Corpus SEP (signal net) — les trois statistiques × les trois
    modèles nuls détectent tous le signal sans ambiguïté

| Statistique | topology-only | group-resample-only | combined |
|---|---|---|---|
| Cohesion_A | percentile 100, z=4.33 | percentile 100, z=4.18 | percentile 100, z=4.15 |
| Cohesion_B | percentile 100, z=19.1 | percentile 100, z=11.6 | percentile 100, z=20.1 |
| Cohesion_C | percentile 100, z=7.36 | percentile 100, z=4.18 | percentile 100, z=7.82 |

Aucune des 9 combinaisons ne discrimine sur ce cas facile — attendu, ce
n'est pas le cas qui doit trancher le choix.

### 3.2 Corpus TWIN (population homogène) — résultat DÉCISIF pour le
    choix du modèle nul

| Statistique | topology-only | group-resample-only | combined |
|---|---|---|---|
| Cohesion_A | percentile 99.5, z=2.12 | **percentile 50.0, z=0.0** | percentile 99.2, z=2.10 |
| Cohesion_B | percentile 100, z=31.7 | **percentile 50.0, z=0.0** | percentile 100, z=30.4 |
| Cohesion_C | percentile 100, z=14.6 | **percentile 50.0, z=0.0** | percentile 100, z=15.8 |

**`group-resample-only` répond correctement « aucune distinction » (z=0.0
exact, les trois statistiques) sur un cas où, par construction, aucune
distinction ne peut exister.** `topology-only` (et `combined`, qui hérite
du même défaut) déclare au contraire une significativité massive
(z jusqu'à 31.7) — un **faux positif net**, confirmé par construction :
casser la topologie détruit la régularité cyclique de TOUT le graphe, pas
seulement celle du groupe candidat, donc la comparaison mesure « ce
corpus a-t-il une structure globale non aléatoire ? », une question
différente de celle que Gate I doit trancher (« CE groupe candidat est-il
plus cohérent qu'un groupe de même taille tiré du même graphe ? »).

**C'est la confirmation empirique directe de l'hypothèse posée par le
porteur du projet** : les deux stratégies de modèle nul testent deux
hypothèses différentes, et seule `group-resample-only` répond à la
question réellement posée par Gate I. `topology-only` reste utilisable
comme diagnostic secondaire (« ce corpus a-t-il une structure globale
suspecte ? ») mais **ne doit jamais servir seul de modèle nul principal
de Gate I** — l'utiliser seul aurait produit ici une fausse relation
"DISCOVERED" à partir d'un corpus rigoureusement homogène.

### 3.3 Corpus PARTIAL (signal réel mais bruité, 80 %/20 %) — cas
    limite, résultat honnête et pas encore tranché

| Statistique | topology-only | group-resample-only | combined |
|---|---|---|---|
| Cohesion_A | percentile 100, z=3.17 | percentile 93.8, z=1.62 | percentile 100, z=2.94 |
| Cohesion_B | percentile 100, z=11.2 | percentile 93.8, z=1.87 | percentile 100, z=11.4 |
| Cohesion_C | percentile 100, z=5.64 | percentile 93.8, z=1.62 | percentile 100, z=5.98 |

Sous `group-resample-only` — le modèle nul retenu par la Sec. 3.2 comme
seul valide pour la question de Gate I — **les trois statistiques
atterrissent toutes au même niveau, juste sous le seuil conventionnel de
95 %/z=1.96**, pour ce cas délibérément difficile et de petite taille
(groupe de 20, `N_null=200`). Ce n'est pas un échec de la calibration :
c'est une mesure honnête de la puissance réelle, limitée, de ces trois
statistiques sur ce cas précis avec cette taille d'échantillon — les
valeurs `topology-only`, plus élevées, sont probablement partiellement
gonflées par le même artefact que la Sec. 3.2 vient de démontrer, donc
**ne doivent pas être lues comme la vraie force du signal**.

**Conséquence directe pour la suite** : aucune des trois statistiques,
seule, ne résout de façon nette le cas V4 (futur, non construit) sous le
modèle nul jugé valide. Soit `N_null`/la taille de groupe doivent
augmenter, soit une statistique combinée doit être testée, soit ce type
de cas doit assumer une issue `AMBIGUOUS` plutôt que `DISCOVERED` — les
trois options restent ouvertes, aucune n'est tranchée ici.

### 3.4 Corpus PURE_NULL (5 répétitions, jauge de faux positifs)

Sur 15 essais (5 répétitions × 3 statistiques) par variante de modèle
nul, au seuil informel de percentile 95 :

- `group-resample-only` : 1/15 dépasse 95 (Cohesion_B, répétition #0,
  percentile 97.0).
- `topology-only` : 0/15 dépasse 95.
- `combined` : 0/15 dépasse 95.

Taux compatibles avec un taux de faux positifs nominal proche de 5 %,
**mais l'échantillon (15 essais) est bien trop petit pour calibrer quoi
que ce soit précisément** — rapporté honnêtement comme une jauge
grossière, pas une estimation fiable. Observation à surveiller sans la
sur-interpréter : `Cohesion_B` tend à donner des percentiles plus élevés
que `Cohesion_A`/`Cohesion_C` sur du bruit pur dans cet échantillon limité
(ex. 97.0, 88.5, 87.0, 93.0 sur les 5 répétitions en `group-resample-only`
et `topology-only`) — possible biais à la hausse, à vérifier avec
davantage de répétitions avant de faire confiance à `Cohesion_B` seule.

## 4. Pilote Gate H — `contradiction_support`

Sur le groupe cohérent de SEP (20 arêtes, toutes avec prolongement
profondeur 2), remplacement progressif par des arêtes-leurres sans
prolongement (contredisant l'hypothèse dominante du groupe) :

| Scénario | `contradiction_support` |
|---|---|
| cohérent (0 remplacée) | 0.000 |
| bruit léger (1/20 = 5 %) | 0.050 |
| modéré (3/20 = 15 %) | 0.150 |
| contredit (6/20 = 30 %) | 0.300 |

La métrique se comporte exactement comme attendu — linéaire, sans
artefact. Elle ne tranche **pas** la valeur de tolérance `τ` à geler :
c'est un jugement de calibration, pas une propriété mesurable en un seul
passage. Une fourchette provisoire raisonnable, à confirmer sur d'autres
corpus avant tout gel, se situe entre 0.10 et 0.15 (au-delà du bruit
léger, en-deçà du cas nettement contredit) — proposée, pas décidée.

## 5. Ce que cette calibration établit, et ce qu'elle n'établit pas

**Établi, par exécution directe** :
- `group-resample-only` (topologie fixe, ré-échantillonnage de
  l'appartenance au groupe) est le modèle nul qui répond correctement à
  la question de Gate I ; `topology-only`, utilisé seul, produit un faux
  positif net et démontré sur un corpus rigoureusement homogène (TWIN).
  **`topology-only` ne doit pas être le modèle nul principal.**
- La signature multi-profondeur candidate (inchangée depuis l'expérience
  d'identifiabilité) reste calculable et utilisable comme base des trois
  statistiques de cohésion testées.
- `contradiction_support` (Gate H) se comporte de façon monotone et
  prévisible sur un pilote simple.
- Deux erreurs de méthode (pool TWIN hétérogène, percentile saturant)
  ont été trouvées et corrigées avant toute conclusion, pas après.

**Non établi, délibérément** :
- Quelle statistique de cohésion (A, B, C, ou une combinaison) doit être
  gelée — sur le cas facile (SEP) les trois sont équivalentes ; sur le
  cas difficile (PARTIAL) les trois sont indiscernables entre elles et
  toutes sous le seuil conventionnel avec cette taille d'échantillon.
- La valeur de `N_null`, du percentile de décision, ou de la taille de
  groupe à geler pour le futur benchmark verrouillé.
- La règle de correction multi-comparaisons (protocole Sec. 13, item 6)
  — **non testée du tout dans cette calibration**, qui n'a évalué qu'UN
  seul groupe candidat à la fois, jamais le scénario réaliste où Gate I
  doit statuer sur de nombreux groupes candidats simultanément (le
  parallèle direct du max-statistic de P4-U.1). Reste entièrement à
  faire.
- La tolérance exacte `τ` de Gate H.
- Si `topology-only` doit être conservé comme diagnostic secondaire et,
  si oui, comment l'interpréter sans qu'il ne domine le verdict principal.

## 6. Prochaine étape

Conformément à la séquence fixée par le porteur du projet
(`calibration jetable → gel numérique → implémentation minimale`), le
gel numérique n'est pas fait ici. Ce document fournit le tableau
d'aide à la décision demandé (Sec. 3-4) ; la décision de geler (ou de
prolonger la calibration — par exemple sur la correction
multi-comparaisons, jamais testée, ou sur une statistique combinée pour
lever l'ambiguïté du cas PARTIAL) reste à prendre explicitement par le
porteur du projet avant toute écriture de code P4-U.2.
