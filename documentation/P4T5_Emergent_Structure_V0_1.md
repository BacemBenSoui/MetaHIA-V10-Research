# MetaHIA V10 — P4-T.5 : structure émergente depuis une transformation gelée v0.1

Date : 2026-09-22
Statut : **implémenté et vérifié — recouvre partiellement E20-D.17, pas une
clôture de gate**

## 1. Le problème que ce chantier résout

La feuille de route (`documentation/MetaHIA_Roadmap_Complete_v0.5.5_2026-09-17.md`)
posait P4-T.5 comme : « opération figée appliquée à de nouveaux opérandes,
recouvre partiellement E20-D.17 ». `e20d_emergent_structure_v0_1.py`
(E20-D.17) démontre déjà ce principe pour une opération **réifiée**
(`RefObject` produit par `e20d_operation_synthesis_v0_1.synthesize_operation()`,
appliquée via `kernel2.apply_operator()`) : appliquer l'opération à des
opérandes qui n'ont pas besoin de former une relation déjà observée dans
le graphe, et vérifier que le résultat est réellement **nouveau**.

P4-T possède sa propre notion d'« opération apprise » — une
`FrozenTransformation` (gelée via `freeze()`, appliquée via
`blind_replay()`) — mais rien dans P4-T ne vérifiait jusqu'ici que la
structure produite était **nouvelle** par rapport à un ensemble déjà
observé. `blind_replay()` prédit ; il ne compare jamais sa prédiction à
quoi que ce soit.

## 2. Pourquoi une fonction parallèle, pas un appel direct à E20-D.17

Même discipline architecturale que P4-T.6 (qui a refusé de fabriquer un
faux `kernel2.PathRecord` pour appeler `score_candidate()` d'E20-D.19) :
`generate_emergent_structure()` d'E20-D.17 exige un opérateur
**`RefObject`** et l'applique via `kernel2.apply_operator()`, qui produit
littéralement `Node(node_id, kind, (operator.ref, *operandes))` — un seul
ref fixe préfixé aux opérandes, rien de plus. Une `FrozenTransformation`
de P4-T n'est pas de cet ordre : c'est une transformation
positionnelle/de motif réelle (permutation, permutation récursive,
sélection, composition), déjà appliquée par `blind_replay()` — forcer une
`FrozenTransformation` à travers `apply_operator()` échouerait au
typage (ce n'est pas un `RefObject`) ou, pire, jetterait silencieusement
toute la logique de transformation réelle.

`p4t_emergent_structure_v0_1.py` ajoute donc exactement ce qui manque
au-dessus d'un `blind_replay()` **non modifié** : une vérification de
nouveauté (`kernel2.structural_equal`, jamais par sémantique de charge
utile — même discipline que le propre test d'E20-D.17
`test_novelty_check_does_not_use_payload_semantics`) contre un ensemble
`observed` fourni par l'appelant. `frozen.structural_digest` (déjà
canonique et invariant à l'identité des entités depuis P4-T.1 bis) tient
lieu d'identité d'opération, à la place du `RefObject.ref` d'E20-D.17.

## 3. Une vraie frontière de portée, trouvée par exécution directe

`blind_replay()` a en réalité **deux** mécanismes de replay selon la
famille, vérifié avant d'écrire une seule ligne de test :

- **`SELECTION_MAPPING`** (projection, duplication) : replay **ligne par
  ligne, indépendamment** (`_blind_replay_one`) — exactement la forme
  « un opérande nouveau → une structure nouvelle » que ce module suppose.
- **Familles à base de motif** (`REFERENCE_EQUALITY`,
  `COMPARE_PERMUTATION`, `COMPARE_RECURSIVE`) : replay sur un **lot de
  taille identique** au nombre de lignes d'entraînement d'origine — le
  `PATTERN` gelé a lui-même une arité de premier niveau égale à ce
  nombre de lignes (déjà visible dans le cas C02 du benchmark verrouillé,
  qui rejoue sur exactement 3 lignes de holdout fraîches, jamais une à la
  fois).

Conséquence, confirmée par exécution directe avant d'écrire le test
correspondant : appeler `generate_emergent_structure_from_frozen()` avec
un seul opérande contre une famille à base de motif renvoie
correctement `NO_PREDICTION` — **fail-closed, jamais une structure
fabriquée à tort** — plutôt que le `CREATED_EMERGENT` démontré pour
`SELECTION_MAPPING`. Ce n'est pas un bug à corriger : c'est une propriété
réelle du mécanisme sous-jacent, documentée explicitement et gardée par
un test de régression permanent
(`test_pattern_based_family_with_a_single_operand_fails_closed_not_created`).
Étendre ce module aux familles à base de motif (avec un opérande en
forme de lot correcte) et aux familles multi-source de P4-T.4
(`blind_replay_multi_source()`, une convention d'appel entièrement
différente) reste un point d'extension explicitement non traité ici.

## 4. Ce qui est démontré, vérifié par exécution directe

- **Structure réellement nouvelle** : un opérande jamais présent dans
  aucune ligne d'entraînement, contre un `observed` vide → `CREATED_EMERGENT`,
  `novelty_verified=True` — pour `SELECTION_MAPPING` en projection
  (arité 3→1) et en duplication (arité 2→3).
- **Rejet d'un doublon exact** : quand `observed` contient déjà
  exactement la structure prédite (`structural_equal`), le statut devient
  `NOT_NEW` — mirroring le propre test d'E20-D.17
  `test_exact_observed_structure_is_not_claimed_novel`.
- **Refus sur incompatibilité de forme** : un opérande de la mauvaise
  arité, même pour `SELECTION_MAPPING`, renvoie `NO_PREDICTION` plutôt
  que de deviner — la même discipline déjà appliquée par
  `_blind_replay_one`, vérifiée ici à travers ce module.
- **Identité d'opération discriminante** : `operation_digest`
  (= `frozen.structural_digest`) diffère bien entre deux transformations
  gelées différentes (projection vs duplication) — pas un espace réservé
  constant.
- **Provenance préservée** : `result.provenance == result.structure.provenance`,
  toujours `(frozen_id, operand.node_id)`.

8 tests, tous exécutés et confirmés, 0 échec.

## 5. Ce que ce chantier N'établit PAS

- **Le sens sémantique de la structure produite reste Inconnu** —
  exactement le contrat déclaré par E20-D.17 lui-même. Ce module prouve
  que la structure est nouvelle et traçable jusqu'à la transformation qui
  l'a produite, jamais ce qu'elle « signifie ».
- **Couverture générale de toutes les familles P4-T** — voir la
  frontière de portée Sec. 3 : familles à base de motif et multi-source
  non couvertes par ce module (par ce module précisément — le mécanisme
  sous-jacent, lui, sait déjà les rejouer sur un lot correctement
  dimensionné, démontré ailleurs).
- **Une clôture d'E20-D.17 ou d'E20-D** — recouvrement **partiel**, comme
  la feuille de route le formulait dès le départ ; ni ce document ni le
  code ne prétendent fermer quoi que ce soit. `e20d_emergent_structure_v0_1.py`
  reste inchangé et continue de couvrir son propre périmètre (opérateurs
  réifiés issus d'`e20d_operation_synthesis_v0_1.py`).
- **Validation par un tiers** — protocole auto-exécuté par cette session,
  même distinction déjà posée pour M4-M7 et pour P4-T.2.

## 6. Tests

`tests/test_p4t_emergent_structure_v0_1.py` (8 tests) : création à partir
d'un opérande neuf (projection et duplication), rejet d'un doublon exact,
refus fail-closed sur incompatibilité de forme (famille à base de motif
et arité incorrecte au sein de `SELECTION_MAPPING`), discrimination de
l'identité d'opération, préservation de la provenance, type `Node`
ordinaire du résultat.

## 7. Décision

**P4-T.5 = `PARTIAL_E20D17_COVERAGE_VIA_FROZEN_TRANSFORMATION, PASS`**
pour le périmètre `SELECTION_MAPPING`. E20-D reste `OPEN` ; E20-D.17
reste son propre mécanisme distinct, non fermé par ce chantier.
