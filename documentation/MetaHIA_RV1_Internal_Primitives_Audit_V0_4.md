# MetaHIA — Audit R-V-1 des primitives internes V0.4

Date: 2026-09-16

## Objet

Vérification des deux réserves signalées après l'unification `PatternRef`/`SHAPE_PATTERN`.

## Réserve 1 — RefObject opaque dans la récurrence

### Constat reproduit

Avant correction, `_flatten_recurrent_args()` et `_shape_template()` traitaient un `RefObject` comme une feuille. Une structure de la forme :

`O(RefObject(O(A,B)), C)`

ne permettait donc pas à l'exploration récurrente de voir la sous-application `O(A,B)`.

### Correction

Les deux primitives résolvent désormais un `RefObject` lorsqu'il désigne effectivement une `OBSERVATION` récurrente du même opérateur.

L'identité du `RefObject` n'est pas perdue : elle continue d'exister comme identité référentielle ; seule sa structure désignée devient traversable dans ce contexte structurel.

### Test

- flattening: PASS
- shape template: PASS

Résultat: `RESOLVED`

## Réserve 2 — R-V-1 limité à la frontière de l'API

### Constat reproduit

Plusieurs primitives internes utilisaient `==` brut : `_compare_observations`, la recherche de permutations, `aggregate_observations`, et le contrôle `requires_source_equal`.

Ce comportement était dangereux parce que `==` n'exprime pas toujours la politique voulue :

- `NodeRef == NodeRef` reflète l'identité de référence ;
- `RefObject == RefObject` combine identité et contenu de la structure ;
- une contrainte structurale peut nécessiter une comparaison structurelle, et non une égalité d'objet Python.

### Nuance méthodologique importante

Le cas « même `ref_id`, structures différentes » n'est pas une égalité structurelle valide. Il signifie :

`ReferenceEqual(P1,P2) = True`

mais :

`StructuralEqual(P1,P2) = False`

Deux structures différentes sous le même identifiant représentent une incohérence d'état/identité si elles sont censées décrire le même objet, et ne doivent pas être fusionnées silencieusement.

### Correction

Introduction d'une comparaison interne explicite :

- `_structural_eq(a,b)` pour les comparaisons structurelles ;
- `_reference_eq_or_structural_eq(a,b)` pour les contraintes explicitement exprimées comme égalité de source/référence.

Les primitives concernées n'utilisent plus `==` brut dans les décisions structurelles visées par l'audit.

### Tests

- même référence reconnue: PASS
- structure différente non confondue avec identité structurelle: PASS
- `requires_source_equal` sur même référence: PASS
- `requires_source_equal` sur références distinctes: PASS
- contrainte littérale `RefObject` comparée structurellement: PASS

Résultat: `RESOLVED`

## Test de régression

- R-V / PatternRef: 19/19 PASS
- E20-D.1 constructeur/unification: 7/7 PASS
- E20-D cross-representation: 3/3 PASS
- E20-D V0.2: 7/7 PASS
- audit ciblé des deux réserves: 7/7 PASS

## Statut gouvernance

- R-V-1: **CLOSED at internal primitive level for audited paths**
- Réserve RefObject/récurrence: **RESOLVED** pour les primitives E18 auditées
- E20-D: **OPEN**
- E20-D.1 (`PatternRef` / unification structurelle): **PASS_MICROSTRUCTURAL**

## Limite conservée

Cette correction ne constitue pas une preuve générale de conservation de provenance ni une preuve que toutes les futures primitives respecteront automatiquement R-V-1. Toute nouvelle primitive comparant des objets structurés devra utiliser les fonctions de comparaison explicites et être couverte par un test adversarial référence/valeur.
