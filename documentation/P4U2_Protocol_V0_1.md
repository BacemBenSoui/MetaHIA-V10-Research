# MetaHIA V10 — P4-U.2 v0.1 : protocole (Autonomous Structural Relation Discovery) — verrouillé avant tout code

## 0. Statut et rapport au cadrage

```text
P4-U.2 = OPEN_RESEARCH
scope  = AUTONOMOUS STRUCTURAL RELATION DISCOVERY
         (jamais raccourci — même règle de nommage que P4-U.1)
séquence respectée :
    cadrage v0.1 -> v0.2 -> v0.3 (SUPERSEDED sauf v0.3)
    -> investigation empirique (2026-09-23)
    -> expérience d'identifiabilité (2026-09-23)
    -> CE PROTOCOLE v0.1
    -> (à venir) modèle nul finalisé -> benchmark verrouillé
```

Ce document formalise, sans les rouvrir, les décisions déjà gelées par
`documentation/P4U2_Autonomous_Relation_Discovery_V0_3.md` (Gate I,
hiérarchie structure/hypothèse/relation, masquage, portée du pool,
exclusions) et intègre le résultat le plus important de
`documentation/P4U2_Identifiability_Experiment_2026-09-23.md` : Gate I
doit comparer une statistique de groupe à un modèle nul, jamais une
égalité de signature par observation — une nécessité démontrée par
exécution directe, pas une option.

**Toujours aucun code de production écrit.** Ce protocole précède
l'implémentation, exactement comme pour P4-T et P4-U.1. Les valeurs
numériques du modèle nul restent à fixer (Sec. 13) avant tout
benchmark verrouillé — jamais avant ce protocole, jamais après avoir vu
un résultat de holdout.

## 1. Origine et cadrage — inchangé depuis la v0.3

```text
P4-T    : induction de transformation à partir de couples FOURNIS.
P4-U.1  : découverte de COMPOSITIONS de relations déjà étiquetées.
P4-U.2  : découverte de GROUPES D'OBSERVATIONS partageant une
          régularité structurelle observable, sans étiquette
          d'opérateur exploitable, sans dictionnaire sémantique.
```

## 2. Objectif — gelé depuis la v0.3, non renégocié

```text
P4-U.2 — Autonomous Structural Relation Discovery

Découvrir, à partir d'un ensemble d'observations dont les identités
d'opérateurs sont masquées, des groupes d'observations partageant une
régularité structurelle observable indépendante de l'identité nominale
de l'opérateur — sans dictionnaire sémantique, sans relation cible
fournie, et sans accès à la vérité terrain pendant la découverte.
```

**Verrou scientifique central** : démontrer qu'une relation inconnue
est IDENTIFIABLE à partir de sa structure observable — jamais
simplement qu'un algorithme sait clusteriser des objets démunis de
leur nom.

## 3. Entrée et interdits

**Entrée, uniquement** : un ensemble d'observations binaires dont
l'opérateur a été masqué individuellement (Sec. 5).

**Interdit, sans exception** :
```text
dictionnaire sémantique                EXCLU
relation cible fournie                 EXCLUE
ancrage à la vérité terrain pendant
    la découverte                      EXCLU
sélection intelligente du pool         EXCLUE (différée après P4-U.2.1)
synthèse d'opération
    (e20d_operation_synthesis_v0_1.py) EXCLUE
découverte de composition P4-U.1       EXCLUE (orthogonale)
```

## 4. Architecture — vue d'ensemble

```text
G (observations, opérateurs originaux jamais transmis au mécanisme)
        ↓
   masquage individuel (Sec. 5) -- réalisé UNE FOIS, hors ligne, par le
   constructeur du corpus, jamais par le mécanisme lui-même
        ↓
G_masked (seule entrée du mécanisme)
        ↓
   pool structurel objectif (Sec. 6)
        ↓
   caractérisation structurelle -- signature candidate (Sec. 7)
        ↓
   Gate I -- Identifiability (Sec. 8) -- statistique de GROUPE contre
   modèle nul (Sec. 9), jamais une égalité de signature par observation
        ↓ (PASS uniquement)
   groupement / STRUCTURAL_CLASS_HYPOTHESIS (Sec. 10)
        ↓
   Gate H -- validation de l'hypothèse de classe (Sec. 11) --
   contrôle négatif dédié, distinct de Gate I
        ↓ (PASS uniquement)
   interprétation opérationnelle -- relation DÉCOUVERTE (Sec. 10.3)
        ↓
   DISCOVERED / AMBIGUOUS / INSUFFICIENT_STRUCTURAL_INFORMATION /
   REJECTED (Sec. 12)
```

Réutilise strictement `kernel2.discover_paths()`,
`kernel2.build_structural_graph()`, `path_properties()` — aucune
modification. Aucune réactivation des fichiers `e20d_*` morts. Un
module minimal nouveau porte la signature candidate, Gate I, Gate H, et
`STRUCTURAL_CLASS_HYPOTHESIS`.

## 5. Masquage — méthode gelée depuis la v0.3 Sec. 5

```text
Avant masquage (jamais visible du mécanisme) :
    E1 : REL_A(x1, y1)
    E2 : REL_A(x2, y2)
    E3 : REL_B(x3, y3)

Présenté au mécanisme :
    E1 : OP#00001(x1, y1)
    E2 : OP#00002(x2, y2)
    E3 : OP#00003(x3, y3)

Vérité terrain (témoin seul, jamais importée avant le commit) :
    OP#00001 -> REL_A
    OP#00002 -> REL_A
    OP#00003 -> REL_B
```

Chaque observation reçoit un opérateur masqué **individuel et
unique** — jamais partagé entre observations de même origine (Sec. 5
de la v0.3 pour la justification complète). Jamais d'opérateur
`UNKNOWN_RELATION` partagé.

## 6. Pool — portée P4-U.2.1, gelée depuis la v0.3 Sec. 5

```text
pool éligible = { observations binaires valides du corpus,
                   profondeur admissible pour le calcul de la
                   signature (Sec. 7) }
```

Critères **structurels et objectifs uniquement** — jamais un critère
lié au contenu ou à une intuition de regroupement. La sélection
intelligente/sémantique du pool est explicitement différée à un
incrément ultérieur (« P4-U.2.2 », non cadré ici).

## 7. Signature structurelle candidate — testée empiriquement, retenue comme hypothèse de travail pour ce protocole

Reprise de l'expérience d'identifiabilité
(`documentation/P4U2_Identifiability_Experiment_2026-09-23.md`) :

```text
Signature(observation masquée e, profondeur max D=3) =
    ( compte de chemins de profondeur 1 dont le premier pas est e,
      compte de chemins de profondeur 2 dont le premier pas est e,
      compte de chemins de profondeur 3 dont le premier pas est e,
      multiset des séquences de direction observées à ces profondeurs )
```

Calculée exclusivement via `kernel2.discover_paths()` (INCHANGÉ),
filtrée aux chemins dont `steps[0].edge_id == edge.edge_id` de `e`.
**Ce protocole retient cette signature comme point de départ pour le
premier benchmark verrouillé (Sec. 14) — pas comme une définition
scientifiquement close.** Preuve empirique déjà établie (expérience du
2026-09-23) :

- Sépare parfaitement deux relations cachées dont le rôle topologique
  diffère (cas `SEPARABLE`).
- Incapable, par construction, de séparer deux relations cachées au
  rôle topologique rigoureusement identique (cas
  `INSUFFICIENT_STRUCTURAL_INFORMATION`, confirmé, pas un défaut).
- Contient un signal réel mais non déterministe dans un cas de
  chevauchement partiel, révélé uniquement par une statistique de
  groupe correcte (Sec. 8/9), jamais par une égalité exacte par
  observation.

Si le futur benchmark verrouillé (Sec. 14) démontre que cette
signature est insuffisante pour un cas légitimement identifiable, ce
protocole devra être révisé — exactement la discipline déjà appliquée
à la v0.1/v0.2/v0.3 du cadrage lui-même.

## 8. Gate I — Identifiability, spécification formelle

**Changement non négociable par rapport à toute vérification par
égalité de signature** — imposé par l'expérience d'identifiabilité,
pas par choix esthétique :

```text
Gate I(candidat de regroupement C, C = ensemble d'observations masquées) :

    1. Calculer une statistique de cohésion de groupe Cohesion(C) sur
       les signatures (Sec. 7) des membres de C -- PAS une égalité
       stricte, une statistique agrégée (ex. fraction des membres
       partageant un trait de signature donné, ou une mesure de
       dispersion inter-membres).
    2. Générer N_null réplicats du corpus sous un modèle nul (Sec. 9),
       calculer Cohesion(C) sur les groupes correspondants dans chaque
       réplicat.
    3. Comparer Cohesion(C) observée à la distribution nulle
       (percentile, méthode à statistique du maximum si plusieurs
       groupes candidats sont testés simultanément -- même discipline
       de correction multi-comparaisons que P4-U.1 Sec. 7).

    Gate I = PASS  si Cohesion(C) dépasse significativement le modèle
                   nul (seuil à fixer, Sec. 13)
    Gate I = FAIL  sinon -> INSUFFICIENT_STRUCTURAL_INFORMATION
                   (résultat scientifique légitime, jamais un bug)
```

**Preuve empirique que cette spécification est nécessaire** (pas
suffisante en elle-même, mais nécessaire) : l'expérience
d'identifiabilité a montré qu'une vérification par égalité exacte de
signature aurait donné un verdict FAUX (`INSUFFICIENT` au lieu d'un
signal réel, z=3,79, p<0,05) sur un cas de chevauchement partiel — Gate
I telle que spécifiée ici (comparaison de groupe contre modèle nul)
aurait correctement détecté ce signal.

**Exactement comme P4-U.1 (Sec. 14 de sa v0.3)**, tout futur benchmark
verrouillé doit inclure un cas de contrôle délibérément non
identifiable (Gate I = FAIL par construction) — sinon le protocole
risque de devenir une démonstration circulaire.

## 9. Modèle nul — principe gelé (v0.3 Sec. 7), construction encore à déterminer

```text
Objectif :
    casser la cohérence inter-observations qui permet le regroupement,
    tout en conservant les propriétés marginales pertinentes du
    corpus.
```

**Ce protocole ne fixe PAS encore la procédure exacte de
randomisation** — contrairement à P4-U.1, où le modèle nul par pool
(source/cible séparés par étiquette) a pu être défini directement parce
que l'étiquette d'opérateur était CONNUE et EXPLOITABLE pour construire
les pools. Ici, les opérateurs sont masqués individuellement (Sec. 5) —
**il n'existe pas de pool par étiquette à permuter**, puisqu'aucune
étiquette partagée n'existe entre observations avant le regroupement
lui-même. Deux pistes, à trancher empiriquement avant le benchmark
verrouillé (Sec. 13, point 2), non résolues ici :

```text
Piste 1 : permuter les paires (source, cible) du pool éligible tout
          entier (indépendamment de tout regroupement candidat),
          préservant les degrés marginaux du graphe -- teste si LA
          COHÉSION MESURÉE pourrait apparaître par pur hasard
          topologique.
Piste 2 : permuter l'ASSIGNATION des observations aux candidats de
          regroupement, sans toucher au graphe lui-même -- teste si LA
          COMPOSITION DU GROUPE candidat pourrait être un artefact du
          processus de clusterisation plutôt qu'un signal réel.
```

Ces deux pistes répondent à des questions différentes et ne sont pas
substituables l'une à l'autre — le choix (ou la combinaison des deux)
est une décision à prendre avec des données réelles de calibration,
jamais avant.

## 10. Hiérarchie structure / hypothèse / relation — gelée depuis la v0.3 Sec. 3

```text
similarité -> structure commune -> STRUCTURAL_CLASS_HYPOTHESIS (status
UNKNOWN) -> validation (Gate I + Gate H) -> ÉVENTUELLE relation
découverte (interprétation séparée, jamais un renommage automatique)
```

### 10.1 `STRUCTURAL_CLASS_HYPOTHESIS` — contrat gelé depuis la v0.3 Sec. 6

```text
STRUCTURAL_CLASS_HYPOTHESIS
    hypothesis_id
    member_observation_ids
    structural_signature       -- Sec. 7
    support                    -- Cohesion(C) observée, Sec. 8
    contradiction_support      -- jamais ignorée
    status                     -- UNKNOWN par défaut (Hypothesis.status,
                                  kernel2.py, INCHANGÉ)
    provenance

-- Aucun champ relation_name/relation_id sur cet objet, délibérément.
```

### 10.2 Gate H — validation de l'hypothèse de classe (nouvelle, distincte de Gate I)

Gate I (Sec. 8) établit qu'un regroupement candidat est
statistiquement significatif contre le hasard. **Gate H établit
séparément qu'il n'est pas contredit** — même discipline que
`Hypothesis.status` (kernel2.py) qui distingue `SUPPORTED` de
`CONTRADICTED`, jamais fusionnés :

```text
Gate H(STRUCTURAL_CLASS_HYPOTHESIS h) :
    Gate H = REJECTED si contradiction_support non triviale existe
             (ex. un sous-ensemble du groupe candidat présente une
             signature incompatible avec le reste, au-delà du bruit
             déjà toléré par Gate I)
    Gate H = PASS     sinon
```

Détail exact de ce qui constitue une « contradiction non triviale » —
à spécifier avec des données réelles de calibration (Sec. 13, point
3), pas ici.

> **Mise à jour (2026-09-24) : GELÉE.** La calibration prévue ci-dessus
> a été exécutée (campagnes C4→C7,
> `documentation/P4U2_Calibration_Campaign4_2026-09-24.md` à
> `documentation/P4U2_Calibration_Campaign7_VoletC_RealCorpus_2026-09-24.md`)
> et Gate H est maintenant spécifiée et gelée en v1.0 dans
> `documentation/P4U2_Gate_H_V1_0_Frozen_2026-09-24.md` : percentile
> ≥95 %, correction multi-comparaisons par maximum, enveloppe de
> calibration `k≥8` / `group_size∈[20,40]`, `CALIBRATION_INSUFFICIENT`
> (jamais `DISCOVERY`) hors de cette enveloppe. **Enveloppe empirique
> opérationnelle, pas une loi universelle** — voir ce document pour les
> réserves explicites (notamment : comportement non établi hors de
> l'enveloppe, taux de faux positifs cohérent avec le niveau nominal
> mais non prouvé exactement à 5 %).

### 10.3 Interprétation opérationnelle — relation découverte

Une `STRUCTURAL_CLASS_HYPOTHESIS` ayant passé Gate I ET Gate H peut
être interprétée comme une relation découverte — un objet **séparé**,
référençant l'hypothèse validée, jamais un champ ajouté à l'hypothèse
elle-même (Sec. 6 de la v0.3, rappel non négociable).

## 11. Rejeu / validation holdout aveugle

Même discipline mécanique que P4-U.1/P4-T : un témoin séparé, jamais
importé avant le commit des prédictions, vérifié statiquement (absence
de mention dans le code de découverte) et dynamiquement (`sys.modules`
au moment du commit). Une `STRUCTURAL_CLASS_HYPOTHESIS` retenue sur
`G_train` doit être re-testée (Gate I + Gate H) sur un `G_holdout`
disjoint, exactement comme Gate C de P4-U.1 re-teste un motif sur le
holdout.

## 12. Vocabulaire de sortie — gelé depuis la v0.3 Sec. 4

```text
DISCOVERED                          -- Gate I PASS, Gate H PASS, holdout confirmé
AMBIGUOUS                           -- plusieurs regroupements plausibles,
                                        aucun ne domine statistiquement
INSUFFICIENT_STRUCTURAL_INFORMATION -- Gate I FAIL -- résultat scientifique
                                        légitime, jamais un bug
REJECTED                            -- Gate H FAIL (contradiction) ou échec
                                        du holdout (Sec. 11)
```

## 13. Checklist de pré-enregistrement — à figer avant le benchmark verrouillé, jamais après

```text
1.  profondeur maximale de la signature (D, Sec. 7)      -- valeur déjà
    proposée (D=3), à confirmer ou ajuster par calibration
2.  procédure exacte du modèle nul (Sec. 9, piste 1/2/
    combinaison)                                          -- GELÉ
    (2026-09-24) : group-resample-only CORRIGÉ (reproduction complète
    de la procédure de sélection sous le null, campagne 5) --
    topology-only invalidé (campagne 5, faux positif net sur un corpus
    homogène) -- voir P4U2_Gate_H_V1_0_Frozen_2026-09-24.md
3.  définition exacte de "contradiction non triviale"
    (Gate H, Sec. 10.2)                                   -- GELÉ
    (2026-09-24) en v1.0 (percentile≥95% + enveloppe k≥8/
    group_size∈[20,40] ; CALIBRATION_INSUFFICIENT hors enveloppe) --
    voir P4U2_Gate_H_V1_0_Frozen_2026-09-24.md
4.  statistique de cohésion de groupe exacte (Sec. 8,
    point 1 -- ex. fraction de trait partagé, distance
    moyenne de signature, autre)                          -- Cohesion_B
    (distance intra-groupe moyenne) retenue et validée par toute la
    chaîne de calibration C5-C7 ; choix final entre les 3 candidats
    (A/B/C) reste ouvert mais non bloquant
5.  N_null, seuil de percentile (Sec. 8, point 3)          -- percentile
    ≥95% GELÉ pour Gate H (v1.0) ; N_null=200-300 confirmé stable
    (campagne 2 Partie 2C) mais pas formellement gelé pour Gate I
6.  correction multi-comparaisons si plusieurs candidats
    testés simultanément                                  -- GELÉ :
    max-statistique (comme P4-U.1), nécessité démontrée (campagne 4
    Partie 3, 33% de faux positifs sans correction) et robustesse
    confirmée sur 20 graines (campagne 4 Partie 2)
7.  seuils numériques du benchmark verrouillé (Sec. 14)    -- À FIXER
    par calibration sur des corpus JETABLES, jamais sur
    le benchmark verrouillé lui-même (même discipline que
    P4-U.1)
```

**Séquence obligatoire, identique dans l'esprit à P4-U.1** :

```text
protocole v0.1 (ce document) — gelé
        ↓
calibration jetable des valeurs numériques manquantes (checklist ci-dessus)
        ↓
implémentation du module minimal (signature, Gate I, Gate H,
    STRUCTURAL_CLASS_HYPOTHESIS)
        ↓
construction du benchmark verrouillé V1/V2/V3/V4 (Sec. 14)
        ↓
tests déterministes
        ↓
run réel contre le benchmark verrouillé
        ↓
documentation du résultat réel, sans lissage, quel qu'il soit
```

## 14. Cas verrouillés du futur benchmark — quatre catégories, une par résultat de sortie possible

```text
V1 -- régularité clairement identifiable
      (rôle topologique net, ex. hub à fort éventail vs 1-à-1)
      Attendu : Gate I PASS -> Gate H PASS -> holdout confirmé ->
                DISCOVERED

V2 -- deux relations cachées au rôle topologique RIGOUREUSEMENT
      identique (extension du cas TWIN de l'investigation empirique)
      Attendu : Gate I FAIL -> INSUFFICIENT_STRUCTURAL_INFORMATION
      (résultat correct, PAS un échec du mécanisme)

V3 -- contrôle nul pur (aucune régularité injectée, généré par le
      modèle nul lui-même -- même rôle que U3 de P4-U.1)
      Attendu : aucun candidat ne dépasse Gate I -> INSUFFICIENT_
      STRUCTURAL_INFORMATION ou REJECTED selon qu'un regroupement est
      même proposé

V4 -- chevauchement partiel, signal réel mais non déterministe
      (reproduction exacte du cas ayant révélé la faille méthodologique
      de l'expérience d'identifiabilité -- 2026-09-23)
      Attendu : Gate I PASS via la statistique de groupe (Sec. 8) --
      JAMAIS via une égalité de signature par observation -- puis
      Gate H PASS -> DISCOVERED. Ce cas existe SPÉCIFIQUEMENT pour
      garantir que l'implémentation ne régresse jamais vers la
      vérification naïve déjà prouvée fausse.
```

Chaque cas doit être accompagné, avant tout run, d'une démonstration
explicite de son identifiabilité attendue (ou de sa non-identifiabilité
délibérée pour V2/V3) — jamais une assertion abstraite (v0.3 Sec. 3).

## 15. Témoin — format, même discipline que P4-U.1/P4-T

```text
WITNESS[case_id] = {
    expected_gate_i: PASS | FAIL,
    expected_gate_h: PASS | FAIL | NOT_APPLICABLE,
    expected_outcome: DISCOVERED | AMBIGUOUS |
                       INSUFFICIENT_STRUCTURAL_INFORMATION | REJECTED,
    expected_identifiability_proof: référence à la démonstration
        préalable d'identifiabilité (Sec. 14) -- jamais calculée par le
        mécanisme lui-même avant le commit.
}
```

## 16. Ce que ce protocole ne fait pas

Aucun code de production. Aucune valeur numérique fixée (Sec. 13).
Aucun benchmark verrouillé construit (Sec. 14 reste une spécification
de cas, pas des données concrètes). La procédure exacte du modèle nul
(Sec. 9) et la définition exacte de « contradiction non triviale »
(Sec. 10.2) restent des questions ouvertes, à trancher par calibration
empirique, pas par ce document.

## 17. Prochaine étape

Calibration jetable des valeurs numériques manquantes (Sec. 13),
JAMAIS sur le futur benchmark verrouillé lui-même — même discipline
que `documentation/P4U1_Locked_Benchmark_Numeric_Calibration_2026-09-23.md`.
Seulement ensuite : implémentation du module minimal, construction du
benchmark verrouillé V1-V4, tests déterministes, run réel.
