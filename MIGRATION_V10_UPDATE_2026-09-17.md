# MetaHIA V10.0 — rapport de comparaison et de mise à jour (2026-09-17)

## Portée

Ce dépôt (`MetaHIA-V10-Research`) contient exclusivement la lignée de recherche K3 :
`kernel2.py`, les modules E20-D (D1–D19), M3 (fermeture récursive), M4 (cold-start) et M5
(contrôleur métacognitif dynamique). Il est **distinct** du dépôt de production
`MetaHIA-Consolidated-Repo` (`MetaHIA-V6.git`), qui contient l'application complète
(frontend, API, ingestion, persistence, etc.) et n'est pas affecté par cette mise à jour.

L'« ancienne version » comparée ici est donc `research/k3_spike_e13a2/` du dépôt de
production — le seul équivalent réel de cette même lignée de recherche — et non
l'application dans son ensemble.

## Méthode de comparaison

Comparaison fichier par fichier entre `MetaHIA_Source_Clean/` (paquet V10.0 livré) et
`research/k3_spike_e13a2/` (ancienne version, dépôt de production), par exécution directe
(hash SHA-256, exécution des suites de tests des deux côtés), pas par confiance narrative.

## Fichiers manquants identifiés dans le paquet V10.0 et portés

Tous présents dans `research/k3_spike_e13a2/` mais absents du paquet V10.0 livré :

| Élément ancien | Statut | Action |
|---|---|---|
| `loader.py` | manquant | porté tel quel à la racine, import adapté (`kernel2` au lieu de `research.k3_spike_e13a2.kernel`) |
| `corpus/micro_corpus_v001.json` | manquant | porté tel quel dans `corpus/` |
| `corpus/validation_corpus_v001.json` | manquant | porté tel quel dans `corpus/` |
| `tests/test_kernel.py` | manquant | porté → `tests/test_kernel_legacy_v0_1.py` |
| `tests/test_kernel_invariants.py` | manquant | porté → `tests/test_kernel_invariants_legacy_v0_1.py` |
| `tests/test_noderef_refobject.py` | manquant | porté → `tests/test_noderef_refobject_legacy_v0_1.py` |
| `tests/test_patternref_structural_signature.py` | manquant | porté → `tests/test_patternref_structural_signature_legacy_v0_1.py` |
| `tests/test_rv1_propagation.py` | manquant | porté → `tests/test_rv1_propagation_legacy_v0_1.py` |
| `tests/test_ambiguity_probe.py` | manquant | porté → `tests/test_ambiguity_probe_legacy_v0_1.py` |
| `tests/test_apply_applicable_unification.py` | manquant | porté → `tests/test_apply_applicable_unification_legacy_v0_1.py` |
| `tests/test_e13a2_generalization.py` | manquant | porté → `tests/test_e13a2_generalization_legacy_v0_1.py` |
| `tests/test_e14_variable_arity.py` | manquant | porté → `tests/test_e14_variable_arity_legacy_v0_1.py` |
| `tests/test_e15_nested_structures.py` | manquant | porté → `tests/test_e15_nested_structures_legacy_v0_1.py` |
| `tests/test_e16_competing_regularities.py` | manquant | porté → `tests/test_e16_competing_regularities_legacy_v0_1.py` |
| `tests/test_e17_operator_emergence.py` | manquant | porté → `tests/test_e17_operator_emergence_legacy_v0_1.py` |
| `tests/test_e18_tree_shapes.py` | manquant | porté → `tests/test_e18_tree_shapes_legacy_v0_1.py` |
| `tests/test_e19_aggregate_observations.py` | manquant | porté → `tests/test_e19_aggregate_observations_legacy_v0_1.py` |
| `tests/test_validation_corpus.py` | manquant | porté → `tests/test_validation_corpus_legacy_v0_1.py` |

Adaptation faite pour chaque fichier porté : uniquement la ligne d'import
(`research.k3_spike_e13a2.kernel`/`.loader` → `kernel2`/`loader`), aucune autre
modification de logique de test.

## Éléments de l'ancienne version délibérément non portés

| Élément | Raison |
|---|---|
| `research/k3_spike_e13a2/results/run_*.json` | journaux d'exécution historiques, pas du code source ; sans valeur de régression |
| `research/k3_spike_e13a2/README.md` | propre au spike E13-A.2 ; le paquet V10.0 a son propre `documentation/README.md` à jour |
| `research/k3_spike_e13a2/kernel.py` | fichier distinct de `kernel2.py` (API globalement compatible mais implémentation propre au dépôt de production) ; V10.0 reste construit sur `kernel2.py`, la lignée « Kernel V2 Intégrale » |

## Bugs confirmés et corrigés dans `kernel2.py` pendant cette mise à jour

Chaque correction a été vérifiée par exécution directe (échec reproductible avant, passage
après, zéro régression sur les 277 tests) — jamais acceptée sur la base d'une affirmation.

### 1. R-V-1 — `_kernel_values_equal()` traitait deux références différentes comme égales
Bug déjà identifié et documenté à plusieurs reprises plus tôt dans les échanges menant à
cette version : pour deux `RefObject` de références **différentes** mais de structure
coïncidemment égale, la fonction retombait sur `structural_equal(a, b)` et renvoyait `True`
— en violation directe du principe R-V-1 lui-même (« une même valeur portée par deux
références distinctes ne crée pas de coréférence »).
**Correction** : retour explicite à `False` pour toute paire de références différentes ;
ajout d'un helper `_reference_consistency()` (verdict à trois voies EQUAL/DIFFERENT/erreur)
mirroir de celui déjà correct dans `research/k3_spike_e13a2/kernel.py`, dont
`_kernel_values_equal()` délègue désormais.

### 2. Coréférence NodeRef cassée dans `apply_tree_shape()`
`apply_tree_shape()` indexait les variables du gabarit (`ShapeTerm("VAR", n)`, numérotées
par référence **distincte** dans `_shape_template()`) contre la liste **brute, non
dédupliquée** produite par `_flatten_recurrent_args()`. Résultat vérifié par exécution :
sur une observation fraîche `O(O(R,R),S)`, la référence répétée `R` apparaissait 3 fois et
`S` disparaissait complètement (0 fois) dans la structure prédite, au lieu de `R` deux fois
et `S` une fois.
**Correction** : nouvel helper `_flatten_recurrent_args_distinct()` qui déduplique par
`ref_id` exactement comme `_shape_template()` numérote ses variables ; `apply_tree_shape()`
et le calcul de l'arité dans `_same_shape_signature()` s'appuient désormais dessus.

### 3. `compare_tree_shapes()` sans garde no-op
Deux observations littéralement identiques produisaient un `SHAPE_PATTERN` trivial
(source == cible) au lieu de `None`, en contradiction avec le contrat de `compare()`
(« identique : rien à découvrir »).
**Correction** : garde explicite `if src == dst: return None`.

### 4. Incohérence `compare()` / `compare_candidates()` sur les cas résolubles uniquement par tree-shape
Pour un cas construit pour n'être découvrable que via le repli `compare_tree_shapes()`
(aucune permutation positionnelle directe ne réconcilie les observations), `compare()`
renvoyait un `SHAPE_PATTERN` valide tandis que `compare_candidates()` — qui n'avait aucun
repli équivalent — renvoyait un tuple vide. Violation directe de l'invariant permanent
« compare() n'est jamais non-None sans qu'exactement un candidat existe ».
**Correction** : `compare_candidates()` retombe désormais sur `compare_tree_shapes()`
quand la recherche positionnelle directe ne trouve aucune permutation.

## Résultat final

| Mesure | Avant mise à jour | Après mise à jour |
|---|---|---|
| `kernel2.py` SHA-256 | `987839...9ea3d9` | `c76adfd2...0efc9aa9` |
| Tests dans le paquet | 26 (M5 uniquement, dossier `tests/`) | 277 (26 originaux + 251 issus des 15 fichiers legacy portés) |
| Résultat | 157 passed (suite complète du paquet, incluant E20-D/M3/M4) | 277 passed, 0 failed |
| Bugs confirmés par exécution | — | 4, tous corrigés et vérifiés zéro régression |

Aucune modification n'a été faite aux modules E20-D/M3/M4/M5 eux-mêmes, ni à leur
documentation ; seul `kernel2.py` a été corrigé, et la couverture de test a été complétée.
