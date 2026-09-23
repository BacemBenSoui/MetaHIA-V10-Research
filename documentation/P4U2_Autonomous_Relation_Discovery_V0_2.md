# MetaHIA V10 — P4-U.2 : cadrage v0.2 (Autonomous Structural Relation Discovery) — aucun code, aucun protocole verrouillé

> **SUPERSEDED (2026-09-23).** Une seconde revue du porteur du projet a
> affiné trois points avant tout protocole formel : l'identifiabilité
> devient une gate formelle nommée (Gate I) ; la chaîne
> « similarité → relation » est cassée en une hiérarchie à trois
> niveaux (structure/hypothèse/relation, jamais confondus) ; les
> exclusions du premier incrément sont gelées comme liste explicite.
> Remplacé intégralement par
> `documentation/P4U2_Autonomous_Relation_Discovery_V0_3.md`. La
> reformulation de l'objectif et les décisions Q1/Q2/Q3 de ce document
> restent valides et reprises telles quelles dans la v0.3.

## 0. Statut et rapport à la v0.1

Remplace intégralement
`documentation/P4U2_Autonomous_Relation_Discovery_V0_1.md` (conservé
pour l'historique de la revue). La v0.1 avait correctement identifié
l'inventaire réutilisable (Sec. 3 de la v0.1 : `reify_path_link`,
`Hypothesis.status`, `ref_jaccard`/`structural_similarity`) et posé
trois questions ouvertes, mais une revue méthodologique du porteur du
projet (2026-09-23) a identifié une faille plus fondamentale dans le
cadrage lui-même, avant même ces trois questions — corrigée ici.

**Toujours aucun code écrit.** Même discipline que pour P4-U.1 : ce
document reste un cadrage, pas un protocole verrouillé (les seuils, les
cas U1/U2/U3 et le module minimal restent une étape ultérieure,
explicitement hors de ce document — Sec. 10).

## 1. La faille du cadrage v0.1 — un piège de non-identifiabilité

La v0.1 formulait le vide à combler comme « comparer deux arêtes après
avoir retiré/masqué l'identité de leur opérateur ». **Ce cadrage est
nécessaire mais pas suffisant, et dangereux tel quel** : si l'on
compare deux observations binaires en ignorant naïvement leur
opérateur,

```text
op1(a, b)
op2(c, d)
```

deviennent, du point de vue de la forme K3 locale, presque identiques :

```text
BINARY(source, target)
BINARY(source, target)
```

Un algorithme naïf regrouperait alors **toutes** les relations
binaires du graphe entre elles, simplement parce qu'elles partagent la
même forme — un problème de non-identifiabilité structurelle, pas une
découverte.

**Reformulation retenue, remplaçant celle de la v0.1** :

```text
P4-U.2 n'est PAS : « comparer des arêtes après avoir ignoré leur
                     opérateur ».

P4-U.2 EST       : découvrir des classes d'opérateurs partageant un
                    comportement structurel OBSERVABLE, indépendant de
                    leur identité nominale.
```

Conséquence directe pour tout futur protocole : la représentation
utilisée pour comparer deux arêtes ne peut pas être la simple forme
locale `(source, target)` — elle doit capturer un **comportement**
structurel de l'opérateur (typiquement : dans quels contextes de
composition il apparaît, avec quelles autres relations, dans quelles
directions — le même type d'information que `discover_paths()`/
`group_by_skeleton()` de P4-U.1 exploitent déjà pour des opérateurs
CONNUS, mais ici appliqué à des opérateurs dont l'identité elle-même
est masquée). **La construction exacte de cette représentation
« invariante-à-l'identité-mais-sensible-au-comportement » reste
délibérément non résolue par ce document** — c'est la question
centrale que le futur protocole v0.1 devra trancher (Sec. 8, étape 2),
pas ce cadrage.

## 2. Objectif retenu

```text
P4-U.2 — Autonomous Structural Relation Discovery

Découvrir, à partir d'un pool d'observations dont les identités
d'opérateurs ont été masquées, des classes d'opérateurs partageant une
régularité structurelle observable — sans dictionnaire sémantique, sans
relation cible fournie, et sans accès à la vérité terrain pendant la
découverte.
```

**Verrou scientifique central, à ne jamais affaiblir** :

> P4-U.2 doit démontrer qu'une relation inconnue est IDENTIFIABLE à
> partir de sa structure observable — pas simplement qu'un algorithme
> sait clusteriser des objets auxquels on a artificiellement retiré
> leur nom.

## 3. Critère d'identifiabilité — préalable à toute question numérique, ajouté avant les 3 questions de la v0.1

Point ajouté par la revue du porteur du projet, plus fondamental que
les 3 questions ouvertes de la v0.1 : **il faut démontrer, avant toute
exécution, qu'il existe réellement une signature ou un contexte
structurel permettant de distinguer les classes d'un corpus donné.**
Un corpus qui ne satisfait pas cette condition n'est pas un corpus
invalide — c'est un corpus dont la bonne réponse ne peut PAS être
`DISCOVERED`, et ce n'est pas un défaut du mécanisme.

**Vocabulaire de sortie retenu, remplaçant le simple
`UNKNOWN`/`AMBIGUOUS`/`DISCOVERED` de la v0.1** :

```text
DISCOVERED                          -- classe identifiée, gates franchies
AMBIGUOUS                           -- plusieurs regroupements plausibles,
                                        aucun ne domine statistiquement
INSUFFICIENT_STRUCTURAL_INFORMATION -- le corpus lui-même ne contient pas
                                        assez de signal pour distinguer
                                        les classes -- résultat
                                        scientifique LÉGITIME, jamais un
                                        échec à corriger
REJECTED                            -- regroupement proposé mais rejeté
                                        (contrôle négatif, cohérence
                                        insuffisante, etc.)
```

**Piège explicitement à éviter** : construire un corpus où la bonne
réponse est indéductible des informations visibles, puis traiter
`AMBIGUOUS`/`INSUFFICIENT_STRUCTURAL_INFORMATION` comme un bug du
mécanisme à corriger. Le futur protocole v0.1 devra inclure, pour
chaque cas verrouillé, une démonstration préalable et explicite de son
identifiabilité (ou de sa non-identifiabilité délibérée, pour un cas de
contrôle).

## 4. Question 1 (v0.1) résolue — comment simuler une « relation inconnue »

**Méthode retenue : masquage individuel des identités d'opérateur, par
observation, avec vérité terrain cachée réservée à l'évaluation
post-hoc.**

```text
Avant masquage (jamais visible du mécanisme pendant la découverte) :
    E1 : REL_A(x1, y1)
    E2 : REL_A(x2, y2)
    E3 : REL_B(x3, y3)
    E4 : REL_A(x4, y4)
    E5 : REL_B(x5, y5)

Présenté au mécanisme :
    E1 : OP#001(x1, y1)
    E2 : OP#002(x2, y2)
    E3 : OP#003(x3, y3)
    E4 : OP#004(x4, y4)
    E5 : OP#005(x5, y5)

Vérité terrain (témoin seul, jamais vue avant le commit) :
    OP#001 -> REL_A
    OP#002 -> REL_A
    OP#003 -> REL_B
    OP#004 -> REL_A
    OP#005 -> REL_B
```

**Chaque observation reçoit un opérateur INDIVIDUEL et UNIQUE**
(`OP#001`, `OP#002`, ... — jamais republié tel quel), pas un opérateur
partagé par relation d'origine — sinon le masquage laisserait
filtrer, via la simple répétition de l'identité masquée, l'information
que le mécanisme est censé découvrir. **Explicitement rejeté** :
introduire un unique opérateur `UNKNOWN_RELATION` partagé — cela
donnerait au mécanisme une catégorie déjà prête à l'emploi, exactement
ce qu'il doit découvrir lui-même.

Condition ajoutée, non négociable pour tout futur benchmark verrouillé
(Sec. 3) : chaque cas doit être accompagné d'une démonstration que le
corpus est structurellement identifiable (ou délibérément non
identifiable, pour un cas de contrôle dont la réponse attendue est
`INSUFFICIENT_STRUCTURAL_INFORMATION`, jamais `DISCOVERED`).

## 5. Question 2 (v0.1) résolue — portée du pool, sélection différée

**Retenu : ne pas intégrer la sélection sémantique/intelligente du pool
dans le premier incrément (« P4-U.2.1 »).**

```text
P4-U.2.1 :
    pool d'arêtes éligibles
    (critères STRUCTURELS objectifs uniquement -- ex. observation
     binaire valide, profondeur admissible -- jamais un critère lié au
     contenu ou à une intuition de regroupement)
            ↓
    représentation indépendante de l'identité de l'opérateur
    (Sec. 1 -- comportementale, pas la forme locale nue)
            ↓
    caractérisation structurale
            ↓
    clusterisation / hypothèses de relation
            ↓
    validation holdout aveugle
```

Raison : si la sélection du pool ET le regroupement par relation sont
mêlés dans le même incrément, un succès ne permet plus de savoir quelle
partie du système a réellement fonctionné — exactement le type de
confusion que P4-U.1 avait déjà évité en séparant strictement Gate A
(découverte), Gate B (sélection) et Gate C (réplication). La sélection
intelligente/sémantique du pool est explicitement différée à un
incrément ultérieur (« P4-U.2.2 » ou au-delà, non cadré ici).

## 6. Question 3 (v0.1) résolue — pas de réactivation de `e20d_operation_synthesis_v0_1.py`

**Décision : ne pas réactiver `e20d_operation_synthesis_v0_1.py`.**
Son contrat (`IDENTIFIED_EXISTING` / `CREATED_NEW` / `AMBIGUOUS`) est
conçu pour synthétiser une opération à partir d'une relation **déjà
découverte** — un problème différent de celui de P4-U.2, qui part de
plusieurs observations et doit d'abord former l'**hypothèse** qu'une
relation existe.

**Nouveau contrat dédié, à construire pour P4-U.2** (structure de
données proposée, pas encore codée) :

```text
RELATION_HYPOTHESIS
    hypothesis_id
    member_edge_ids          -- les arêtes regroupées sous cette hypothèse
    structural_signature      -- la représentation comportementale (Sec. 1)
    support                   -- preuve en faveur du regroupement
    contradiction_support     -- preuve contre (jamais ignorée)
    status                    -- UNKNOWN par défaut (Hypothesis.status,
                                 kernel2.py, INCHANGÉ -- Sec. 3 de la v0.1)
    provenance
```

**Règle non négociable, répétée depuis la v0.1 et renforcée ici** :
`cluster structurellement cohérent` **n'implique jamais automatiquement**
`relation identifiée`. La promotion d'une `RELATION_HYPOTHESIS` vers un
statut `DISCOVERED` ne peut se faire qu'après le passage explicite des
gates du futur protocole (identifiabilité démontrée + contrôle négatif
+ validation holdout aveugle) — jamais par la seule cohérence du
clustering.

## 7. Risque `O(n²)` — confirmé, mais son optimisation est différée

`structural_similarity()`/`ref_jaccard()` (`e20d_rationalization_v0_1.py`,
vivant) effectuent une comparaison paire-à-paire — une clusterisation
naïve sur `n` candidats est donc potentiellement `O(n²)`, un risque de
faux positifs structurellement plus grand que le compte par squelette
`O(n)` de P4-U.1 (déjà signalé en v0.1, confirmé ici). **Décision
explicite : ne pas chercher à optimiser ce coût avant d'avoir figé ce
qui constitue une unité de comparaison.** Ordre de résolution retenu,
à respecter strictement dans le futur protocole v0.1 :

```text
1. définir la représentation invariante-à-l'identité (Sec. 1)
2. définir l'identifiabilité (Sec. 3)
3. définir le modèle nul (comparable en esprit à Sec. 6/7 de P4-U.1 v0.3,
   mais adapté à une statistique de similarité par paire, pas à un
   compte par squelette)
4. définir la clusterisation elle-même
5. seulement ensuite, si nécessaire, optimiser le coût de calcul
```

Optimiser avant l'étape 1 risquerait d'optimiser un objet scientifique
mal défini.

## 8. Pipeline P4-U.2.1 retenu — vue d'ensemble

```text
identités d'opérateur masquées (Sec. 4)
        ↓
représentation structurelle invariante-à-l'identité (Sec. 1 -- NON
    résolue ici, question centrale du futur protocole v0.1)
        ↓
regroupement de candidats (pool structurel objectif, Sec. 5 --
    sélection intelligente DIFFÉRÉE)
        ↓
réification d'hypothèse (RELATION_HYPOTHESIS, Sec. 6 -- nouveau
    contrat dédié, PAS e20d_operation_synthesis_v0_1.py)
        ↓
validation holdout aveugle (même discipline d'aveuglement mécanique
    que P4-U.1/P4-T -- témoin jamais importé avant le commit)
        ↓
DISCOVERED / AMBIGUOUS / INSUFFICIENT_STRUCTURAL_INFORMATION / REJECTED
    (Sec. 3)
```

**Exclu explicitement de P4-U.2.1** : sélection intelligente/sémantique
du pool (Sec. 5), synthèse d'opération via `e20d_operation_synthesis_v0_1.py`
(Sec. 6), optimisation de la complexité de clusterisation (Sec. 7),
toute réactivation des 4 autres fichiers `e20d_*` morts (confirmés non
pertinents, v0.1 Sec. 3).

## 9. Ce que ce document ne fait toujours pas

Aucun code, aucun seuil numérique, aucun cas verrouillé, aucune
représentation structurelle concrètement spécifiée (Sec. 1 reste une
question ouverte pour le protocole, pas résolue ici), aucun modèle nul
concret. Ce cadrage v0.2 fige uniquement : la reformulation de
l'objectif (Sec. 2), le critère d'identifiabilité et son vocabulaire
de sortie (Sec. 3), la méthode de masquage (Sec. 4), la portée du
premier incrément (Sec. 5), le contrat `RELATION_HYPOTHESIS` sans
réactivation de code mort (Sec. 6), et l'ordre de résolution des
questions techniques restantes (Sec. 7).

## 10. Prochaine étape

Un protocole v0.1 formel pour P4-U.2.1, écrit seulement après
validation explicite de ce cadrage par le porteur du projet, devra
répondre en premier à la question centrale non résolue ici (Sec. 1) :
quelle représentation structurelle, construite uniquement à partir des
primitives K3 déjà existantes (`discover_paths`, `group_by_skeleton`,
`ref_jaccard`/`structural_similarity`), capture un comportement
d'opérateur indépendant de son identité nominale, sans réintroduire de
sémantique ni de dictionnaire de relations. **Toujours aucun code avant
ce protocole.**
