# MetaHIA — E20-D.2
## Découverte d'une transformation structurelle récursive non triviale — V0.1

**Date :** 2026-09-16  
**Statut :** PASS_MICROSTRUCTURAL  
**Périmètre :** spike K3 / E20-D, sans modification de M1 v0.4

### 1. Objectif

Vérifier qu'après l'unification structurelle `PATTERN` / `SHAPE_PATTERN` et la fermeture opérationnelle de R-V-1, E20-D peut découvrir et rejouer une transformation qui n'est pas une simple permutation au niveau supérieur, mais qui contient une transformation elle-même découverte récursivement dans une sous-structure.

### 2. Construction expérimentale

Chaque observation contient deux slots structurés : une source et une cible.

Source :

`O(*x,*y,*z)`

Cible :

`O(*y,*x,*z)`

La transformation entre les deux slots est donc :

`source_position -> target_position`

avec une permutation interne des deux opérandes de `O`.

Aucune signification sémantique n'est donnée à `O`, `x`, `y` ou `z`.

### 3. Chaîne observée

`observations`

→ projection des positions `(source,target)`

→ `Compare` générique sur les colonnes

→ `Compare` récursif sur les sous-observations

→ réification du sous-pattern

→ réification du pattern englobant

→ `PatternRef`

→ `Apply`

→ prédiction sur un holdout inédit.

### 4. Résultats

- découverte d'un `COMPARE_RECURSIVE` : PASS
- présence d'au moins un `nested_pattern` dans le pattern découvert : PASS
- replay sur trois observations holdout non utilisées pour la découverte : PASS
- inversion interne `(*x,*y) -> (*y,*x)` correctement reproduite : PASS
- aucune consultation de payload externe : PASS
- aucune règle sémantique ou dictionnaire : PASS
- régression des suites E20-D précédentes : PASS
- suite complète `tests/` : PASS

### 5. Portée de la preuve

Le test démontre une capacité de découverte structurelle récursive pour une transformation composée d'une permutation interne. Il ne démontre pas l'identification d'une fonction arbitraire sur des valeurs opaques, ni la fermeture générale de toutes les transformations possibles.

### 6. Réserves conservées

`E20-D` reste **OPEN**.

La preuve actuelle ne ferme pas :

- l'apprentissage générique de transformations non permutatives sur des atomes opaques ;
- la conservation générale de provenance/information dans toutes les compositions ;
- la fermeture récursive autonome vers de nouvelles opérations hors du langage structurel actuellement représenté.

### 7. Décision

`E20-D.2 = PASS_MICROSTRUCTURAL`.

La prochaine étape doit tester une transformation composée dont la structure n'est pas réductible à une seule permutation récursive, sans introduire d'opérateur sémantique spécialisé.
