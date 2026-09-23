# MetaHIA V10 — P4-U.1 : découverte non supervisée de compositions structurelles (protocole, avant tout code)

> **Remplacé par la v0.2 avant toute implémentation**
> (`documentation/P4U1_Unsupervised_Compositional_Pattern_Discovery_V0_2.md`),
> suite à une revue méthodologique du porteur du projet (2026-09-23) qui a
> identifié plusieurs points bloquants (modèle nul non défini
> précisément, absence de correction pour comparaisons multiples,
> Gate B/C non quantitatives, `min_depth` non imposé). **Ce document
> v0.1 est conservé tel quel pour l'historique de la revue** — aucune
> implémentation ne doit s'appuyer dessus ; se référer exclusivement à
> la v0.2.

## 0. Statut

```text
P4-U.1 = OPEN_RESEARCH
scope  = UNSUPERVISED_COMPOSITIONAL_PATTERN_DISCOVERY
exclu  = NOT_AUTONOMOUS_RELATION_DISCOVERY
```

**Aucun code n'existe encore pour ce chantier.** Ce document fixe le
protocole et la conception des cas verrouillés AVANT toute
implémentation — exactement la discipline déjà appliquée à P4-T
(`documentation/P4T_Structural_Transformation_Induction_V0_1.md`), où
le protocole a précédé `p4t_structural_transformation_induction_v0_1.py`.
Rien dans ce document ne doit être lu comme déjà implémenté ou déjà
testé.

## 1. Origine et cadrage — ce que ce document N'EST PAS

`P4-U` n'existe nulle part dans l'historique du projet avant ce
document (vérifié directement par recherche dans `documentation/*.md`
et `release_manifest.json`, 2026-09-23 — aucune occurrence hors des
deux mentions de la distinction `STRUCTURAL_TRANSFORMATION_INDUCTION`
vs `AUTONOMOUS_DISCOVERY_GENERAL` déjà présentes dans le document
P4-T). Ce document **crée** ce nouvel axe expérimental, explicitement
borné, sans prétendre qu'il était déjà prévu par une roadmap
antérieure.

**Distinction essentielle, retenue telle qu'établie** :

```text
P4-U.1 = découverte non supervisée de COMPOSITIONS structurelles
         sur un graphe à relations DÉJÀ ÉTIQUETÉES
         (ex. MERE_DE, TRAVAILLE_DANS, ENFANT_DE...)

P4-U.2 (futur, non défini ici) = découverte autonome de relations
         INCONNUES — reste à définir seulement après avoir vu les
         résultats de P4-U.1, pas avant
```

Relation avec P4-T (`p4t_structural_transformation_induction_v0_1.py`) :
P4-T reçoit un couple `(source, cible)` explicitement pendant
l'entraînement — c'est de l'**induction de transformation à partir de
paires données**, jamais contesté par ce document. P4-U.1 ne reçoit
**que** le graphe : aucune paire, aucune cible, aucun squelette cible,
aucune hypothèse de transformation. C'est une capacité différente, pas
une extension incrémentale de P4-T.

## 2. Objectif exact

> Découvrir, sans cible désignée, une composition structurelle
> récurrente (un squelette de chemin) dans un graphe dont les relations
> (arêtes) sont déjà nommées — et démontrer que cette découverte est
> **distinguée du bruit**, pas seulement fréquente.

Le second membre de cette phrase est le point le plus important de ce
protocole (Sec. 6) : `discover_paths()` énumère déjà *tous* les
chemins, et les relations sont déjà nommées — un squelette peut donc
être « retrouvé » simplement parce qu'il apparaît plusieurs fois, sans
que cela démontre une régularité structurelle réelle. Un critère de
succès qui se limiterait à « le squelette injecté est retrouvé »
serait insuffisant et n'est **pas** retenu ici.

## 3. Entrée et interdits stricts

**Entrée, uniquement** :

```text
Graphe
 ├── nœuds
 └── arêtes étiquetées (relations déjà connues du domaine)
```

**Interdit, explicitement, au pipeline de découverte lui-même** :

- ❌ aucune relation cible fournie
- ❌ aucun couple source → cible fourni
- ❌ aucun squelette cible fourni
- ❌ aucune hypothèse de transformation fournie
- ❌ aucun dictionnaire sémantique (règle déjà en vigueur dans tout ce
  projet, M1-M6/E20-D/P4-T — non renégociée ici)

## 4. Pipeline — uniquement l'existant, plus un module minimal nouveau

Aucune nouvelle couche de raisonnement n'est ajoutée tant que
l'existant peut démontrer le phénomène recherché — le même principe
déjà appliqué par P4-T.5/P4-T.6 (adaptateurs parallèles, jamais de
mécanisme dupliqué sans raison).

```text
kernel2.discover_paths(graph, start=None, end=None, max_depth=..., max_paths=...)
        -- EXISTANT, aucune modification. Avec start=end=None (le
           défaut), énumère tous les chemins simples du graphe sans
           filtrage sémantique -- confirmé par lecture directe du code
           (kernel2.py, discover_paths()) : c'est déjà une énumération
           structurelle aveugle, pas une recherche guidée par une
           cible.
        ↓
group_by_skeleton()  -- NOUVEAU, minimal. Regroupe les PathRecord
           retournés par squelette (operator/direction, le même type
           de clé que `_skeleton_key()` déjà utilisé de façon
           dispersée dans m6_corpus_from_organization_v0_1.py et les
           autres bâtisseurs de corpus M6 -- généralisé ici en un
           point unique, réutilisable, plutôt que redupliqué une
           cinquième fois).
        ↓
support filtering + comparaison au contrôle négatif (Sec. 6)
        -- NOUVEAU, minimal.
        ↓
candidate selection, seuil PRÉ-ENREGISTRÉ avant tout accès au holdout
        -- NOUVEAU, minimal (Gate B, Sec. 5).
        ↓
kernel2.generalize_path_pattern(paths, pattern_id=...)
        -- EXISTANT, aucune modification. Compatibilité stricte déjà
           vérifiée par le code (longueur identique, squelette
           structurellement égal, intersection des contraintes de
           référence -- jamais union). Confirmé par lecture directe.
        ↓
freeze -> FrozenPattern (Sec. 8)  -- NOUVEAU, mêmes disciplines de
           durcissement que p4t.freeze() (P4-T.1/P4-T.1bis).
        ↓
kernel2.replay_path_pattern_holdout(pattern, holdout, start, ...)
        -- EXISTANT, aucune modification.
```

**Explicitement PAS réactivé** : les 5 fichiers `e20d_*` déjà
identifiés comme morts (`e20d_operation_synthesis_v0_1.py`,
`e20d_emergent_structure_v0_1.py`, `e20d_operator_behavior_v0_1.py`,
`e20d_operator_relation_v0_1.py`, `e20d_property_discovery_v0_1.py`)
— confirmé par recherche directe d'appelants (2026-09-23) : aucun,
hors de leurs propres tests. Les réintroduire dans P4-U.1 ajouterait de
la surface non validée sans raison démontrée.

## 5. Les trois portes (Gates A/B/C)

**Gate A — Découverte.** Le squelette cible apparaît parmi les
candidats énumérés par le pipeline — jamais cherché directement, jamais
fourni en entrée.

**Gate B — Sélection.** Le squelette est retenu selon une règle FIXÉE
AVANT tout accès au graphe holdout : support minimal + règle
structurelle (ex. longueur, absence de contradiction) + seuil
pré-enregistré dans le protocole (pas ajusté après coup pour faire
correspondre le résultat au holdout — même discipline anti-triche que
P4-T Gate E).

**Gate C — Généralisation.** Le squelette gelé (`FrozenPattern`, Sec.
8) est rejoué à l'aveugle (`replay_path_pattern_holdout`) sur un graphe
holdout totalement séparé, avec des identités de nœuds disjointes de
celles de l'entraînement — la régularité doit rester observable.

Un cas qui échoue à Gate A, B, ou C n'est pas un échec du protocole :
c'est un résultat honnête (voir U2/U3, Sec. 9).

## 6. Contrôle négatif — le point le plus important de ce protocole

Comparer uniquement `support réel > seuil absolu` serait insuffisant :
un squelette peut être fréquent simplement parce que le corpus a été
construit ainsi, sans refléter une régularité structurelle réelle.

Le critère de succès retenu est donc :

```text
support réel dans le graphe structuré
              >
support attendu sous un graphe nul/randomisé
   conservant les marges pertinentes
   (fréquences d'étiquettes, topologie choisie)
```

et jamais seulement `support réel > seuil`. Le graphe nul/randomisé
(`G_negative`, Sec. 7) est un artefact de premier ordre du protocole,
pas une vérification secondaire.

## 7. Split au niveau du graphe, jamais des chemins

```text
G_train      -- graphe d'entraînement, entités E_train
G_holdout    -- graphe de test, entités E_holdout, DISJOINTES de E_train
G_negative   -- graphe nul/randomisé, mêmes marges de fréquence d'étiquette
                et la même topologie choisie que G_train, jamais dérivé
                d'un mélange train/holdout
```

Split explicitement **au niveau du graphe entier**, jamais
`chemin 1 → train, chemin 2 → holdout` : un même motif présent des
deux côtés reproduirait exactement le type de fuite que P4-T.1/P4-T.1bis
ont dû corriger (identités d'entraînement lisibles après coup), ici
transposée au niveau du graphe plutôt que de l'enregistrement.
Identités de nœuds complètement distinctes entre `G_train` et
`G_holdout`, vérifiées programmatiquement (même discipline que
`test_no_holdout_entity_is_reused_from_training_within_any_case` déjà
utilisé pour P4-T/M6).

## 8. Ce qui est gelé — `FrozenPattern`

```text
FrozenPattern
├── skeleton              -- operator_sequence + direction_sequence
│                            (kernel2.PathPattern porte déjà ces deux
│                             champs séparément, confirmé par lecture
│                             directe)
├── depth                 -- longueur du chemin
├── structure             -- position_groups (contraintes de
│                            co-référence, intersection déjà calculée
│                            par generalize_path_pattern())
├── support_train         -- nombre de chemins d'entraînement ayant
│                            produit l'abstraction (len(source_path_ids)
│                            au moment du gel, jamais conservé au-delà)
└── discovery_metadata    -- seuil utilisé, règle de sélection, horodatage
```

**Explicitement EXCLU du gel** (même discipline de durcissement que
P4-T.1/P4-T.1bis, Sec. 6.1/6.2 du document P4-T) :

- `source_path_ids` lui-même (le champ existe bel et bien sur
  `kernel2.PathPattern`, confirmé par lecture directe du code — c'est
  précisément le type de champ porteur d'identité d'entraînement que
  P4-T a dû apprendre à exclure ; ne pas le reproduire ici serait une
  régression méthodologique, pas une simplification)
- toute identité de nœud d'entraînement (`NodeRef`, `node_id`)
- toute information de holdout, sous quelque forme que ce soit, avant
  la phase de rejeu (Gate C)

## 9. Les trois cas verrouillés minimum requis (U1 / U2 / U3)

Chaque cas est un triplet `(G_train, G_holdout, G_negative)` avec des
entités totalement disjointes entre les trois graphes d'un même cas, et
entre les cas eux-mêmes.

**U1 — régularité réelle.** Un squelette fortement supporté, injecté
délibérément à la fois dans `G_train` et `G_holdout` (même régularité
structurelle, entités disjointes). Attendu : découvert (Gate A),
sélectionné (Gate B), répliqué au holdout (Gate C) — le cas de succès
complet.

**U2 — motif fréquent mais accidentel.** Un squelette fréquent
uniquement dans `G_train` (jamais reproduit dans `G_holdout`). Attendu :
peut être découvert et même sélectionné en entraînement (Gate A/B
peuvent passer), mais **doit échouer honnêtement à Gate C** — un
`FrozenPattern` qui échoue au rejeu holdout n'est pas un bug du
protocole, c'est exactement le résultat que ce cas doit produire. Un
protocole qui « corrigerait » ce résultat pour le faire réussir serait
disqualifié par construction (même principe que P4-T Gate E : ne
jamais fabriquer un succès).

**U3 — bruit pur.** `G_negative`, un graphe nul/randomisé, structuré
pour conserver les mêmes marges de fréquence d'étiquette et la même
topologie que `G_train` sans porter aucune régularité injectée.
Attendu : ne doit produire aucun statut de découverte comparable à U1
— le support d'un squelette candidat dans `G_negative` sert de ligne de
base pour le contrôle de la Sec. 6, pas seulement de test isolé.

Ces trois cas, ensemble, distinguent **DISCOVERY** de **FREQUENCY
DETECTION** — la question méthodologique centrale de tout ce protocole.
Un futur benchmark verrouillé pourra ajouter des cas U1b/U2b/U3b pour
couvrir plusieurs profondeurs/tailles de squelette, mais U1/U2/U3 sont
le minimum requis avant tout premier résultat.

## 10. Ce que ce protocole ne prétend PAS démontrer

- **Pas la découverte autonome d'une relation totalement inconnue.**
  Aucun nom d'arête n'est jamais inconnu du système — `MERE_DE`,
  `TRAVAILLE_DANS`, etc. restent toujours des relations déjà nommées
  dans le graphe d'entrée. Le système découvre éventuellement une
  **composition** (`MERE_DE → FRERE_DE`, `A → R → B`), jamais
  « il existe une relation inconnue entre X et Y ». C'est exactement la
  réserve `NOT_AUTONOMOUS_RELATION_DISCOVERY` du statut (Sec. 0).
- **Pas la fermeture d'`E20-D`.** Ce protocole, même entièrement
  réussi, ne fermerait qu'une capacité supplémentaire (composition sans
  paire cible fournie) — pas les 4 conditions globales d'E20-D (voir
  `documentation/P4T_Structural_Transformation_Induction_V0_1.md`
  Sec. 9.1).
- **Pas un substitut à un futur P4-U.2** (émergence de relation
  inconnue), qui reste explicitement à définir seulement après avoir vu
  les résultats réels de P4-U.1 — pas avant, pour éviter de concevoir
  une expérience autour d'un résultat qu'on n'a pas encore.

## 11. Ce que P4-U.1 apporterait — la progression devient lisible

```text
P4-T
paires (source, cible) fournies
        ↓
induction de transformation
        ↓
rejeu à l'aveugle
        ↓
nouvelle structure

P4-U.1
graphe seul
        ↓
énumération de chemins
        ↓
découverte de motif
        ↓
sélection de motif
        ↓
gel
        ↓
rejeu à l'aveugle sur holdout
```

Un niveau de non-supervision supplémentaire, réel mais explicitement
borné — pas encore le niveau final (`P4-U.2`, non défini).

## 12. Prochaine étape — non commencée par ce document

Une fois ce protocole validé explicitement par le porteur du projet,
l'implémentation suivra exactement cette architecture, dans cet ordre
(même discipline que P4-T : protocole avant implémentation, tests
déterministes avant tout run réel) :

1. Module minimal nouveau (`group_by_skeleton()`, filtrage de support +
   comparaison au contrôle négatif, sélection à seuil pré-enregistré,
   `freeze()` vers `FrozenPattern`) — réutilisant strictement
   `kernel2.discover_paths()`/`generalize_path_pattern()`/
   `replay_path_pattern_holdout()`, sans modification de `kernel2.py`.
2. Cas verrouillés U1/U2/U3 codés en trois fichiers séparés (cas/témoin/
   exécuteur), même discipline de verrouillage statique (texte + AST)
   et dynamique (`sys.modules`) que `p4t_locked_benchmark_runner_v0_1.py`/
   `_v0_2.py`.
3. Tests déterministes sur données synthétiques, AVANT tout run réel
   contre un corpus construit pour ce chantier.
4. Documentation du résultat réel, sans lissage, quel qu'il soit —
   y compris si U2 échoue à Gate C comme attendu, ou si U1 échoue de
   façon inattendue (un résultat à documenter honnêtement, pas à
   corriger silencieusement).

**Ce document ne code rien.** Il fixe le cadrage à valider avant toute
ligne d'implémentation.
