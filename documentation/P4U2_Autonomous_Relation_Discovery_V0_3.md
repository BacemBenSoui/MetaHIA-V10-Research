# MetaHIA V10 — P4-U.2 : cadrage v0.3 (Gate I formelle, hiérarchie structure/hypothèse/relation, exclusions gelées) — aucun code, aucun protocole verrouillé

## 0. Statut et rapport à la v0.2

Remplace intégralement
`documentation/P4U2_Autonomous_Relation_Discovery_V0_2.md` (conservé
pour l'historique de la revue — sa reformulation de l'objectif et ses
trois décisions Q1/Q2/Q3 restent valides et reprises ici sans
changement). Une seconde revue du porteur du projet (2026-09-23) a
affiné trois points avant tout protocole formel : (1) l'identifiabilité
devient une **gate formelle nommée (Gate I)**, pas seulement un
critère prosaïque ; (2) la chaîne « similarité → relation » est
explicitement cassée en une hiérarchie à trois niveaux
(structure/hypothèse/relation), pour ne jamais confondre structure,
dérivation et statut épistémique ; (3) les exclusions du premier
incrément sont gelées comme une liste explicite, pas seulement
implicites dans le texte.

**Toujours aucun code écrit.**

## 1. Définition scientifique — inchangée depuis la v0.2, reformulée légèrement

```text
P4-U.2 — Autonomous Structural Relation Discovery

Découvrir, à partir d'un ensemble d'observations dont les identités
d'opérateurs sont masquées, des GROUPES D'OBSERVATIONS partageant une
régularité structurelle observable indépendante de l'identité nominale
de l'opérateur — sans dictionnaire sémantique, sans relation cible
fournie, et sans accès à la vérité terrain pendant la découverte.
```

Changement de formulation, délibéré : la v0.2 parlait de « classes
d'opérateurs » ; cette v0.3 parle de « groupes d'observations ». Ce
n'est pas cosmétique — voir Sec. 3 : le mécanisme ne doit jamais
présumer qu'un « opérateur » au sens relationnel existe avant d'avoir
validé le groupement.

**Verrou scientifique central, inchangé** : P4-U.2 doit démontrer
qu'une relation inconnue est IDENTIFIABLE à partir de sa structure
observable — jamais simplement qu'un algorithme sait clusteriser des
objets démunis de leur nom.

## 2. Gate I — Identifiability (nouvelle, formelle, précoce)

Élevée du statut de simple critère (v0.2 Sec. 3) à celui de **gate
nommée**, au même rang que les Gates A/B/C de P4-U.1 — vérifiée **avant
et indépendamment** de toute tentative de regroupement :

```text
Gate I — Identifiability

Un cas n'est expérimentalement valide que si, APRÈS masquage des
identités d'opérateur (Sec. 5), les classes cibles restent
distinguables à partir des seules informations autorisées (la
représentation structurelle du futur protocole, Sec. 8 point 1 — non
encore spécifiée ici).

Gate I = PASS  -> le cas peut légitimement produire DISCOVERED,
                  AMBIGUOUS ou REJECTED (Sec. 4)
Gate I = FAIL  -> résultat attendu et obligatoire : 
                  INSUFFICIENT_STRUCTURAL_INFORMATION
                  (jamais un échec du mécanisme à corriger)
```

**Règle non négociable** : un cas de contrôle délibérément non
identifiable (Gate I = FAIL par construction) doit exister dans tout
futur benchmark verrouillé, exactement comme U3 (contrôle nul) existe
déjà pour P4-U.1 — sinon le protocole risquerait de devenir une
démonstration circulaire (jamais testé que le mécanisme sait
reconnaître l'absence de signal, seulement qu'il sait en trouver quand
il y en a).

## 3. Hiérarchie structure / hypothèse / relation — jamais confondues

Correction apportée par la seconde revue à la formulation de la v0.2
(« plusieurs observations → hypothèse d'une relation inconnue »,
jugée trop directe) :

```text
INTERDIT :
    similarité  ⇒  relation

OBLIGATOIRE, en trois étapes distinctes, jamais fusionnées :
    similarité
        ↓
    structure commune              (observation structurelle brute)
        ↓
    hypothèse de classe structurale (STRUCTURAL_CLASS_HYPOTHESIS,
                                      Sec. 6 -- statut UNKNOWN, jamais
                                      encore interprétée comme
                                      « relation »)
        ↓
    validation (Gate I déjà passée, puis futures gates de
                significativité et de holdout, non encore spécifiées)
        ↓
    ÉVENTUELLE relation découverte  (DISCOVERED -- une INTERPRÉTATION
                                      OPÉRATIONNELLE de la classe
                                      validée, jamais un renommage
                                      automatique de l'hypothèse)
```

**Pourquoi c'est important** : ceci est exactement l'invariant déjà en
vigueur dans ce dépôt (Sec. 1 de la v0.2 citait déjà
`m3_recursive_structural_closure_v0_1.py:13`, « DERIVED structures are
never treated as epistemic evidence ») — appliqué ici à un niveau
supplémentaire : une CLASSE STRUCTURALE n'est pas encore une RELATION,
et une RELATION proposée n'est pas encore un fait SUPPORTED. Trois
statuts, jamais réductibles l'un à l'autre.

## 4. Vocabulaire de sortie — inchangé depuis la v0.2

```text
DISCOVERED                          -- classe validée, interprétée comme
                                        relation (Sec. 3)
AMBIGUOUS                           -- plusieurs regroupements plausibles,
                                        aucun ne domine
INSUFFICIENT_STRUCTURAL_INFORMATION -- Gate I = FAIL (Sec. 2) -- résultat
                                        scientifique légitime
REJECTED                            -- regroupement proposé mais rejeté
                                        (contrôle négatif insuffisant)
```

## 5. Q1 — méthode de masquage — inchangée depuis la v0.2

Masquage individuel par observation (`OP#001`, `OP#002`, ... jamais
partagé entre observations de même origine), vérité terrain cachée
réservée à l'évaluation post-hoc, jamais d'opérateur
`UNKNOWN_RELATION` partagé. Voir v0.2 Sec. 4 pour l'exemple complet,
non répété ici.

## 6. Q3 — contrat dédié, renommé pour respecter la hiérarchie Sec. 3

**Renommage délibéré depuis la v0.2** : `RELATION_HYPOTHESIS` devient
`STRUCTURAL_CLASS_HYPOTHESIS` — le nom lui-même ne doit jamais
présumer qu'une relation a été identifiée avant validation (Sec. 3).

```text
STRUCTURAL_CLASS_HYPOTHESIS
    hypothesis_id
    member_observation_ids    -- les observations regroupées (jamais
                                  "member_edge_ids" -- une observation,
                                  pas encore une arête relationnelle
                                  nommée)
    structural_signature       -- représentation comportementale
                                  (non spécifiée ici, Sec. 8 point 1)
    support
    contradiction_support      -- jamais ignorée
    status                     -- UNKNOWN par défaut (Hypothesis.status,
                                  kernel2.py, INCHANGÉ)
    provenance

-- Champ absent délibérément : aucun champ "relation_name" ou
   "relation_id" sur cet objet. L'interprétation "relation découverte"
   (Sec. 3) est produite SÉPARÉMENT, seulement après DISCOVERED, comme
   un objet distinct référençant l'hypothèse validée -- jamais un champ
   de l'hypothèse elle-même.
```

Toujours PAS de réactivation de `e20d_operation_synthesis_v0_1.py`
(inchangé depuis la v0.2 Sec. 6 — son contrat IDENTIFIED_EXISTING/
CREATED_NEW/AMBIGUOUS reste pour une relation DÉJÀ découverte, un
problème différent).

## 7. Modèle nul — principe fixé, conception différée après la représentation

Point ajouté par la seconde revue, plus précis que la v0.2 Sec. 7 :
**le modèle nul doit être conçu APRÈS la représentation structurelle,
jamais avant**, avec un objectif précis :

```text
Objectif du futur modèle nul de P4-U.2 :
    casser la cohérence inter-observations qui permet le regroupement,
    tout en conservant les propriétés marginales pertinentes du
    corpus.
```

**Différence explicite avec P4-U.1, reconnue comme un risque accru** :
P4-U.1 disposait d'un support de squelette relativement naturel
(compte de chemins) et d'une correction par maximum-statistique déjà
éprouvée (v0.3 Sec. 7). **Pour P4-U.2, la statistique de cohésion à
comparer au modèle nul reste à déterminer** — ce n'est pas une simple
adaptation du maximum-statistique existant, c'est une question ouverte
de plein droit, à résoudre seulement après la représentation
structurelle (Sec. 8 point 1). Ordre de résolution, inchangé depuis la
v0.2 Sec. 7 : représentation → identifiabilité (Gate I) → modèle nul →
clusterisation → optimisation du coût.

## 8. P4-U.2.1 — pipeline et exclusions gelées

```text
observations à opérateurs masqués (Sec. 5)
        ↓
représentation indépendante de l'identité de l'opérateur
        ↓
caractérisation structurelle
        ↓
Gate I -- Identifiability (Sec. 2)
        ↓ (PASS uniquement)
groupement / hypothèses de classe structurale
        ↓
réification de l'hypothèse (STRUCTURAL_CLASS_HYPOTHESIS, Sec. 6)
        ↓
validation aveugle holdout (même discipline d'aveuglement mécanique
    que P4-U.1/P4-T)
        ↓
DISCOVERED / AMBIGUOUS / INSUFFICIENT_STRUCTURAL_INFORMATION / REJECTED
    (Sec. 4)
```

**Exclusions gelées pour P4-U.2.1** (liste explicite, remplace la
formulation dispersée de la v0.2) :

```text
sélection intelligente du pool        EXCLUE (différée, v0.2 Sec. 5)
dictionnaire sémantique                EXCLUE
relation cible fournie                 EXCLUE
ancrage à la vérité terrain pendant
    la découverte                      EXCLUE
synthèse d'opération
    (e20d_operation_synthesis_v0_1.py) EXCLUE (Sec. 6)
découverte de composition P4-U.1       EXCLUE (orthogonal -- P4-U.2 ne
                                          tente pas simultanément de
                                          découvrir des compositions ;
                                          les deux mécanismes restent
                                          séparés)
```

## 9. Ce que ce document ne fait toujours pas

Aucun code, aucun seuil numérique, aucun cas verrouillé. La
représentation structurelle invariante-à-l'identité (Sec. 8, étape 1)
et la statistique de cohésion pour le modèle nul (Sec. 7) restent
délibérément non spécifiées — questions centrales du futur protocole
formel, pas de ce cadrage.

## 10. Prochaine étape — investigation empirique préalable, pas encore le protocole

Décision explicite du porteur du projet : avant d'écrire le protocole
expérimental, déterminer, à partir du dépôt existant, **quelles
informations structurelles peuvent réellement différencier deux
opérateurs opaques** — c'est-à-dire construire la liste des candidats
sérieux pour la représentation de la Sec. 8, étape 1, en s'appuyant
uniquement sur les primitives K3 déjà existantes (`discover_paths`,
`group_by_skeleton`, `ref_jaccard`/`structural_similarity`,
`path_properties`), sans en inventer une nouvelle avant d'avoir vérifié
ce qui est déjà mesurable. Cette investigation reste un exercice de
lecture/mesure directe, pas une implémentation de P4-U.2 lui-même — son
résultat conditionnera l'écriture du protocole v0.1 formel.

## 11. Investigation empirique menée (2026-09-23) — résultat

Faite, par exécution directe (jamais spéculée) — détail complet dans
`documentation/P4U2_Structural_Signature_Investigation_2026-09-23.md`.
Résumé :

- `path_properties().branching_at_start/end` (kernel2.py, INCHANGÉ) est
  un candidat réel : il sépare parfaitement deux relations cachées qui
  diffèrent par leur rôle topologique local (éventail de sortie,
  continuation avale), mais échoue **par construction, confirmé
  empiriquement** quand deux relations cachées partagent exactement le
  même rôle local — exactement la frontière que Gate I (Sec. 2) doit
  détecter et rapporter comme `INSUFFICIENT_STRUCTURAL_INFORMATION`.
- `ref_jaccard`/`structural_similarity` (`e20d_rationalization_v0_1.py`,
  INCHANGÉ) s'est révélé **non informatif** pour la similarité de TYPE
  de relation — il mesure la co-occurrence d'entité, un phénomène
  différent, à ne jamais confondre dans un futur protocole. Une erreur
  de test (opérateurs non masqués dans un premier essai) avait
  d'abord suggéré un faux signal — corrigée avant toute conclusion,
  pas après.
- Aucune nouvelle primitive n'a été nécessaire : la représentation
  manquante (Sec. 8, étape 1) peut vraisemblablement se construire en
  combinant des mesures `path_properties`/`discover_paths` déjà
  existantes à plusieurs profondeurs, pas en inventant un nouveau
  mécanisme de bas niveau.

Toujours aucun protocole verrouillé, aucun code P4-U.2 — cette
investigation fournit une base empirique pour la question ouverte,
elle ne la referme pas.

## 12. Expérience d'identifiabilité sur une signature candidate multi-profondeur (2026-09-23)

Étape distincte, explicitement demandée par le porteur du projet entre
l'investigation (Sec. 11) et le futur protocole v0.1 — détail complet
dans
`documentation/P4U2_Identifiability_Experiment_2026-09-23.md`. Une
signature combinant profondeurs 1/2/3 (via `discover_paths`,
INCHANGÉ) a été testée comme HYPOTHÈSE, pas comme définition acquise,
sur trois corpus :

- Un cas `SEPARABLE` confirmé (signal net, sans ambiguïté).
- Un cas `INSUFFICIENT_STRUCTURAL_INFORMATION` confirmé, y compris par
  une vérification indépendante au niveau du groupe (signal
  authentiquement nul, pas un artefact de méthode).
- Un cas révélant un **constat méthodologique plus important que les
  verdicts eux-mêmes** : une comparaison de signature par égalité
  exacte par observation a d'abord donné un verdict FAUX
  (`INSUFFICIENT` alors qu'un signal réel existait, 80 % contre 20 %,
  z=3,79, statistiquement significatif) — corrigé en remplaçant cette
  vérification par une statistique de groupe. **Conséquence directe
  pour Gate I (Sec. 2)** : elle ne peut pas se limiter à une égalité de
  signature, elle doit intégrer une comparaison statistique de groupe
  face à un modèle nul, dès sa première version — pas une conséquence
  théorique anticipée, une nécessité démontrée par exécution.

Toujours aucun protocole verrouillé, aucun code P4-U.2. Ce commit clôt
l'enquête exploratoire préalable — pas une validation de l'algorithme
P4-U.2 lui-même.